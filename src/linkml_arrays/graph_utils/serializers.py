"""Graph-based serializers for LinkML labeled array models.

The serializers in this module operate on an ``ObjectGraph`` rather than
directly traversing instantiated LinkML objects. This separates graph
construction from serialization and provides a common intermediate
representation for YAML, YAML with external array storage, HDF5, and
Zarr serialization.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import h5py
import numpy as np
import xarray as xr
import zarr
from pydantic import BaseModel
from xarray import DataTree

from linkml_arrays.graph_utils.graph import GraphNode, ObjectGraph


class YAMLGraphArraySerializer:
    """Serialize an ObjectGraph to a YAML representation with external arrays.

    Object-valued LinkML attributes are serialized as nested YAML
    mappings, while array-valued attributes are written to external files
    using a caller-provided array writer. The YAML document stores
    references to the external array files.
    """

    def __init__(
        self,
        graph: ObjectGraph,
        output_dir: Path,
        write_array: Callable,
        array_format: str,
    ):
        """Initialize the serializer.

        Parameters
        ----------
        graph
            Object graph to serialize.
        output_dir
            Directory in which external array files are written.
        write_array
            Callable responsible for writing an array to disk.
        array_format
            Name of the external array format recorded in the YAML output.
        """
        self.graph = graph
        self.output_dir = output_dir
        self.write_array = write_array
        self.array_format = array_format

        self.serialized: dict[UUID, dict[str, Any]] = {}

    def make_filename(self, node: GraphNode, slot_name) -> Path:
        """Construct an output filename for an array-valued attribute.

        Array filenames are derived from the identifier of the owning object
        when available. Otherwise, the filename is derived from the identifier
        of the parent object together with the intervening LinkML attribute.
        """
        if node.identifier is not None:
            return self.output_dir / f"{node.identifier}.{slot_name}"

        if node.incoming:
            edge = node.incoming[0]
            parent = self.graph[edge.parent]

            if parent.identifier is not None:
                return self.output_dir / f"{parent.identifier}.{edge.slot_name}.{slot_name}"

        raise ValueError(f"Cannot determine filename for {node.class_name}")

    def serialize(self, dir_path=None):
        """Serialize the graph into a nested YAML-compatible dictionary.

        Nodes are serialized in dependency order so that referenced child
        objects are available before their parents are constructed.

        Returns
        -------
        dict
            Serialized representation of the root object.
        """
        for node in self.graph.dependency_order():
            self.serialized[node.key] = self.serialize_node(node, dir_path)

        return self.serialized[self.graph.root]

    def serialize_node(self, node, dir_path):
        """Serialize a single graph node.

        Array-valued attributes are replaced with external array references,
        object-valued attributes are replaced with serialized child mappings,
        and scalar attributes are copied directly.
        """
        result = {}

        # TODO: discuss whether there is a way to also get rid of using the schema here, e.g.
        # can we purely use ObjectGraph?
        for slot_name, value in node.values.items():
            metadata = node.value_metadata.get(slot_name)
            if metadata is not None and metadata.is_array:
                filename = self.make_filename(
                    node,
                    slot_name,
                )

                output = self.write_array(
                    value,
                    filename,
                )
                yaml_file_value = f"./{output.as_posix()}"

                result[slot_name] = {
                    "source": [
                        {
                            "file": yaml_file_value,
                            "format": self.array_format,
                        }
                    ]
                }
            else:
                result[slot_name] = value

        for edge in node.outgoing:
            child = self.serialized[edge.child]

            if edge.multivalued:
                result.setdefault(edge.slot_name, []).append(child)
            else:
                result[edge.slot_name] = child

        return result


class Hdf5GraphSerializer:
    """Serialize an ObjectGraph into an HDF5 hierarchy.

    Each graph node becomes an HDF5 group, scalar attributes become
    group attributes, array-valued attributes become datasets, and
    object-valued attributes become child groups.
    """

    def __init__(
        self,
        graph: ObjectGraph,
        h5file: h5py.File,
    ):
        """Initialize the HDF5 serializer.

        Parameters
        ----------
        graph
            Object graph to serialize.
        h5file
            Open HDF5 file that will receive the serialized model.
        """
        self.graph = graph
        self.h5file = h5file

        self.groups: dict[UUID, h5py.Group] = {}

    def serialize(self):
        """Write the complete graph to the HDF5 file.

        Nodes are visited in hierarchy order so that parent groups are created
        before child groups.
        """
        root = self.graph[self.graph.root]
        self.groups[root.key] = self.h5file

        for node in self.graph.hierarchy_order():
            self.serialize_node(node)

    def serialize_node(self, node: GraphNode):
        """Serialize a single graph node as an HDF5 group."""
        if node.key not in self.groups:
            edge = node.incoming[0]
            parent_group = self.groups[edge.parent]
            group = parent_group.create_group(edge.slot_name)
            self.groups[node.key] = group

        group = self.groups[node.key]

        for slot_name, value in node.values.items():
            metadata = node.value_metadata.get(slot_name)
            if metadata is not None and metadata.is_array:

                group.create_dataset(
                    slot_name,
                    data=value,
                )
            else:
                group.attrs[slot_name] = value


class ZarrGraphSerializer:
    """Serialize an ObjectGraph into a Zarr hierarchy.

    Each graph node becomes a Zarr group, scalar attributes become group
    attributes, array-valued attributes become Zarr arrays, and
    object-valued attributes become child groups.
    """

    def __init__(
        self,
        graph: ObjectGraph,
        root: zarr.Group,
    ):
        """Initialize the Zarr serializer.

        Parameters
        ----------
        graph
            Object graph to serialize.
        root
            Root Zarr group that will receive the serialized model.
        """
        self.graph = graph
        self.root = root

        self.groups: dict[UUID, zarr.Group] = {}

    def serialize(self):
        """Write the complete graph to the Zarr hierarchy.

        Nodes are visited in hierarchy order so that parent groups are created
        before child groups.
        """
        root_node = self.graph[self.graph.root]
        self.groups[root_node.key] = self.root

        for node in self.graph.hierarchy_order():
            self.serialize_node(node)

    def serialize_node(self, node: GraphNode):
        """Serialize a single graph node as a Zarr group."""
        if node.key not in self.groups:
            edge = node.incoming[0]
            parent_group = self.groups[edge.parent]

            group = parent_group.create_group(edge.slot_name)
            self.groups[node.key] = group

        group = self.groups[node.key]

        for slot_name, value in node.values.items():
            metadata = node.value_metadata.get(slot_name)
            if metadata is not None and metadata.is_array:
                group.create_array(
                    slot_name,
                    data=np.asarray(value),
                )
            elif isinstance(value, BaseModel):
                continue
            else:
                group.attrs[slot_name] = value


class YamlGraphSerializer:
    """Serialize an ObjectGraph into a nested YAML representation.

    All arrays remain embedded within the YAML document and object-valued
    LinkML attributes are represented as nested mappings.
    """

    def __init__(
        self,
        graph: ObjectGraph,
    ):
        """Initialize the YAML serializer.

        Parameters
        ----------
        graph
            Object graph to serialize.
        """
        self.graph = graph
        self.serialized: dict[UUID, dict] = {}

    def serialize(self) -> dict:
        """Serialize the graph into a nested YAML-compatible dictionary.

        Nodes are serialized in dependency order so that child objects are
        available before their parents.

        Returns
        -------
        dict
            Serialized representation of the root object.
        """
        for node in self.graph.dependency_order():
            self.serialized[node.key] = self.serialize_node(node)
        assert self.graph.root is not None
        return self.serialized[self.graph.root]

    def serialize_node(self, node: GraphNode) -> dict:
        """Serialize a single graph node into a YAML-compatible mapping."""
        result = dict(node.values)

        for edge in node.outgoing:
            child = self.serialized[edge.child]

            if edge.multivalued:
                result.setdefault(edge.slot_name, []).append(child)
            else:
                result[edge.slot_name] = child

        return result


class XarrayGraphSerializer:
    """Serialize an ObjectGraph into an xarray DataTree hierarchy.

    Scalar-valued attributes are stored as dataset attributes, array-valued
    attributes become xarray DataArrays, and object-valued attributes become
    child DataTree nodes.
    """

    def __init__(
        self,
        graph: ObjectGraph,
    ):
        """Initialize the serializer."""
        self.graph = graph

    def serialize(self) -> DataTree:
        """Serialize the complete ObjectGraph to an xarray DataTree."""
        if self.graph.root is None:
            raise ValueError("ObjectGraph has no root node.")

        root = self.graph[self.graph.root]
        return self._serialize_node(root)

    def _serialize_node(
        self,
        node: GraphNode,
    ) -> DataTree:
        """Serialize a graph node and its children to a DataTree node.

        Scalar values are stored as dataset attributes. Array valued child
        nodes are represented as coordinates or data variables, while other
        child nodes are recursively represented as nested DataTree nodes.

        Parameters
        ----------
        node
            Graph node to serialize.

        Returns
        -------
        DataTree
            DataTree node representing the supplied graph node and its
            descendants.
        """
        attrs: dict[str, Any] = {}
        coords: dict[str, xr.DataArray] = {}
        data_vars: dict[str, xr.DataArray] = {}
        children: dict[str, DataTree] = {}

        for slot_name, value in node.values.items():
            metadata = node.value_metadata.get(slot_name)
            if metadata is not None and metadata.is_array:
                data_vars[slot_name] = self._make_data_array(
                    node=node,
                    slot_name=slot_name,
                    value=value,
                )
            else:
                attrs[slot_name] = value

        for edge in node.outgoing:
            child = self.graph[edge.child]

            if self._is_array_node(child):
                array_slot_name, value = self._find_array_value(child)
                data = np.asarray(value)

                filter_metadata = {
                    name: child_value
                    for name, child_value in child.values.items()
                    if name != array_slot_name
                }

                if data.ndim == 1:
                    if coords:
                        dims = (next(iter(coords)),)
                    else:
                        dims = (edge.slot_name,)

                    coords[edge.slot_name] = xr.DataArray(
                        data=data,
                        dims=dims,
                        attrs=filter_metadata,
                    )

                else:
                    data_vars[edge.slot_name] = self._make_data_array(
                        node=child,
                        slot_name=array_slot_name,
                        value=data,
                        attrs=filter_metadata,
                    )

            else:
                children[edge.slot_name] = self._serialize_node(child)

        dataset = xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs=attrs,
        )

        tree = DataTree(dataset=dataset)

        for name, child_tree in children.items():
            tree[name] = child_tree

        return tree

    @staticmethod
    def _is_array_node(
        node: GraphNode,
    ) -> bool:
        """Return whether a graph node contains an array-valued attribute.

        Parameters
        ----------
        node
            Graph node to inspect.

        Returns
        -------
        bool
            `True` if the node contains an array-valued attribute.
        """
        return any(metadata.is_array for metadata in node.value_metadata.values())

    @staticmethod
    def _find_array_value(
        node: GraphNode,
    ) -> tuple[str, Any]:
        """Return the first array-valued attribute stored on a graph node.

        Parameters
        ----------
        node
            Graph node to inspect.

        Returns
        -------
        tuple[str, Any]
            Name and value of the array-valued attribute.

        Raises
        ------
        ValueError
            If the node does not contain an array-valued attribute.
        """
        # TODO: works for now, but can we expect multiple arrays in a node?
        for name, value in node.values.items():
            if node.value_metadata[name].is_array:
                return name, value

        raise ValueError(f"{node.class_name} does not contain an array-valued value.")

    @staticmethod
    def _array_dims(
        node: GraphNode,
        slot_name: str,
        value: Any,
    ) -> tuple[str, ...]:
        """Determine xarray dimensions for an array-valued graph attribute.

        Declared graph dimensions are used when their number matches the
        dimensionality of the array. Otherwise, generic dimension names are
        generated.

        Parameters
        ----------
        node
            Graph node containing the array-valued attribute.
        slot_name
            Name of the array-valued attribute.
        value
            Array value whose dimensions are determined.

        Returns
        -------
        tuple[str, ...]
            Dimension names to use for the xarray DataArray.
        """
        data = np.asarray(value)
        dimensions = node.value_metadata[slot_name].dimensions

        if dimensions is not None and len(dimensions) == data.ndim:
            return dimensions

        return tuple(f"dim_{i}" for i in range(data.ndim))

    def _make_data_array(
        self,
        node: GraphNode,
        slot_name: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
    ) -> xr.DataArray:
        """Construct a DataArray for an array-valued graph attribute.

        Parameters
        ----------
        node
            Graph node containing the array-valued attribute.
        slot_name
            Name of the array-valued attribute.
        value
            Array value to store in the DataArray.
        attrs
            Optional attributes to attach to the DataArray.

        Returns
        -------
        xr.DataArray
            DataArray containing the supplied value and graph-derived
            dimensions.
        """
        data = np.asarray(value)

        return xr.DataArray(
            data=data,
            dims=self._array_dims(
                node=node,
                slot_name=slot_name,
                value=data,
            ),
            attrs=attrs,
        )
