"""Backend independent graph representation of labeled array linkml model.

This module provides an intermediate representation between a LinkML model
and its serialzied forms. Rather than having each serializer traverse the
Pydantic object hierarchy, a model is first converted into an `ObjectGraph`.
Serializers and deserializers than operate on this graph.

The mapping from LinkML to the graph is as follows:
- Each instance of a LinkML class is represented by a `GraphNode`.
- Scalar and array-valued slots are stored in `GraphNode.values`.
- Object / class valued slots are represented by `GraphEdge` objects connecting
the corresponding nodes.
- LinkML slot properties needed during serialization, such as `multivalued` and
`inlined`, are retained on the `GraphEdge`.
- The value of a LinkML identifier slot, when present, is stored separately as
`GraphNode.identifier`.

Every graph node also has a UUID key. This key is internal to the graph and should not
be confused with a LinkML identifier. A LinkML identifier is part of the data model and
may be meaningful outside the graph, whereas the UUID only provides an unambigous way to
refer to a node and construct edges between nodes. This is the case even in the absence
of a LinkML identifier and thus can always be used to represent a relationship between
2 `GraphNode` in an `ObjectGraph`.

`SchemaView` provides the LinkML schema information needed to construct the `ObjectGraph`.
In particular, it allows for distinguishing ordinary values and arrays from relationships
to other LinkML class instances and to retain relevant slot metadata.

The resulting `ObjectGraph` acts as a boundary between the LinkML labeled array object
model and storage backends. YAML, HDF5, Zarr, xarray and other (future) serializers can
therefore share the same representation of objects and relationships while remaining
responsible for their own storage-specific layout.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import h5py
import numpy as np
import xarray as xr
import yaml
import zarr
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition
from pydantic import BaseModel
from xarray import DataTree


@dataclass(slots=True)
class GraphValueMetadata:
    """Describe properties of a value stored in an ObjectGraph.

    GraphValueMetadata contains backend-independent information needed to
    interpret a value without referring back to its LinkML schema. When an
    ObjectGraph is constructed from a LinkML model, this information is
    derived from the corresponding slot definition.
    In particular, `dimensions` represents the dimensions declared by a
    LinkML array-valued slot. A value with dimensions is therefore considered
    an array, while `None` indicates a non-array value.
    This class exists to allow serializers to work without serializers.

    Note: while only including dimensions currently, this could be expanded
    """

    # TODO: we should discuss what extra general fields could be useful here I think
    dimensions: tuple[str, ...] | None = None

    @property
    def is_array(self) -> bool:
        """Return True if graph value is an array."""
        return self.dimensions is not None


@dataclass(slots=True)
class GraphEdge:
    """Directed edge representing an object-valued LinkML attribute.

    Each edge corresponds to a LinkML attribute whose range is another
    class. The edge stores both the graph topology and the relevant
    LinkML slot metadata required during serialization and
    deserialization.

    Attributes
    ----------
    parent
        Key of the parent node.
    child
        Key of the child node.
    slot_name
        Name of the LinkML attribute represented by this edge.
    multivalued
        Whether the attribute is multivalued.
    inlined
        Whether the attribute is serialized inline according to the
        LinkML schema.
    """

    parent: UUID
    child: UUID
    slot_name: str
    multivalued: bool = False
    inlined: bool = False

    def __repr__(self) -> str:
        """Return a concise string representation of the graph edge.

        The returned representation shows the parent node, the LinkML
        attribute represented by the edge, and the child node in the form::

            <parent> --<slot_name>--> <child>

        Returns
        -------
        str
            Human-readable representation of the graph edge.
        """
        return f"{self.parent} --{self.slot_name}--> " f"{self.child}"


@dataclass(slots=True)
class GraphNode:
    """Node representing a LinkML object in a labeled array model.

    A node corresponds to a single instance of a LinkML class. During
    serialization, the original Pydantic object is stored in ``obj``.
    During deserialization, scalar and array-valued attributes are stored
    in ``values`` until the object can be reconstructed. References to
    other LinkML objects are represented by graph edges rather than being
    stored directly as attribute values.

    Attributes
    ----------
    obj
        Instantiated Pydantic object when serializing, or ``None`` during
        deserialization.
    class_name
        Name of the corresponding LinkML class.
    identifier
        Value of the LinkML identifier slot, if one exists.
    values
        Mapping from attribute names to scalar or array-valued
        attributes. Object-valued attributes are represented by outgoing
        edges instead.
    incoming
        Graph edges corresponding to object-valued attributes pointing to
        this node.
    outgoing
        Graph edges corresponding to object-valued attributes originating
        from this node.
    """

    class_name: str
    obj: BaseModel | None = None
    identifier: str | None = None
    values: dict[str, Any] = field(default_factory=dict)
    value_metadata: dict[str, GraphValueMetadata] = field(default_factory=dict)
    incoming: list[GraphEdge] = field(default_factory=list)
    outgoing: list[GraphEdge] = field(default_factory=list)
    key: UUID = field(default_factory=uuid4, init=False)

    @property
    def parents(self) -> list[UUID]:
        """First order parents of the node."""
        return [e.parent for e in self.incoming]

    @property
    def children(self) -> list[UUID]:
        """First order children of the node."""
        return [e.child for e in self.outgoing]

    def __repr__(self):
        """Return a concise string representation of the graph node.

        The returned representation includes the LinkML class name and, if
        available, the value of its identifier slot.

        Returns
        -------
        str
            Human-readable representation of the graph node.
        """
        return f"GraphNode(" f"{self.class_name}, " f"id={self.identifier!r})"


class ObjectGraph:
    """Graph representation of a LinkML labeled array model.

    The graph provides a serialization-independent representation of a
    LinkML model. Each node corresponds to a LinkML class instance,
    object-valued attributes are represented as directed edges, and
    scalar and array-valued attributes remain stored on their
    corresponding nodes.

    The graph may be constructed either from an instantiated LinkML model
    or from serialized representations such as YAML, HDF5, or Zarr.

    Attributes
    ----------
    nodes
        Mapping from node keys to graph nodes.
    root
        Key of the root node.
    _object_index
        Mapping from the identity of instantiated Pydantic objects to
        node keys. Used to avoid rediscovering objects during graph
        construction from an in-memory LinkML model.
    _identifier_index
        Mapping from LinkML identifier values to node keys for efficient
        lookup of referenced objects.
    """

    def __init__(self):
        """Initialize an empty ObjectGraph.

        Creates an empty graph with no nodes or root object. Internal indices
        for object identity and LinkML identifiers are initialized to support
        graph construction from instantiated LinkML models and serialized
        representations.
        """
        self.nodes: dict[UUID, GraphNode] = {}
        self.root: UUID | None = None
        self._identifier_index: dict[str, UUID] = {}
        self._object_index: dict[int, UUID] = {}

    @classmethod
    def from_root(
        cls,
        root: BaseModel,
        schemaview: SchemaView,
    ) -> "ObjectGraph":
        """Construct an ObjectGraph from an instantiated LinkML model.

        Traverses the LinkML object mode and constructs
        a graph representation in which each LinkML class instance becomes a
        graph node. Object-valued attributes are represented as directed
        edges between nodes, while scalar and array-valued attributes remain
        associated with their corresponding node.

        The resulting graph provides a serialization-independent
        representation of the model that can subsequently be serialized to
        hierarchical formats such as YAML, HDF5, or Zarr.

        Parameters
        ----------
        root
            Root object of the instantiated LinkML model.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        ObjectGraph
            Graph representation of the LinkML model.
        """
        graph = cls()
        root_node = graph._discover(root, schemaview)
        graph.root = root_node.key

        return graph

    @classmethod
    def from_hdf5(
        cls,
        source: str | Path,
        schemaview: SchemaView,
        root_class: str,
    ) -> "ObjectGraph":
        """Construct an ObjectGraph from an HDF5 representation of a LinkML model.

        Traverses an HDF5 hierarchy and constructs a graph representation in
        which each HDF5 group corresponding to a LinkML class instance
        becomes a graph node. Group attributes are stored as scalar
        attributes of the node, datasets become array-valued attributes, and
        nested groups become directed edges representing object-valued
        LinkML attributes.

        The resulting graph provides a serialization-independent
        representation of the model that can subsequently be deserialized
        into instantiated LinkML objects.

        Parameters
        ----------
        source
            Path to the HDF5 file.
        schemaview
            SchemaView describing the LinkML schema.
        root_class
            Name of the LinkML root class represented by the root HDF5
            group.

        Returns
        -------
        ObjectGraph
            Graph representation of the LinkML model stored in the HDF5
            file.

        Raises
        ------
        ValueError
            If ``root_class`` is not defined in the schema.
        """
        graph = cls()

        with h5py.File(source, "r") as f:
            schema_class = schemaview.get_class(root_class)

            if not schema_class:
                raise ValueError(f"Root class {root_class} not found in schema.")

            root = graph._discover_hdf5_group(
                group=f,
                class_definition=schema_class,
                schemaview=schemaview,
            )
            graph.root = root.key

        return graph

    @classmethod
    def from_zarr(
        cls,
        source: str | Path,
        schemaview: SchemaView,
        root_class: str,
    ) -> "ObjectGraph":
        """Construct an ObjectGraph from a Zarr representation of a LinkML model.

        Traverses a Zarr hierarchy and constructs a graph representation in
        which each Zarr group corresponding to a LinkML class instance
        becomes a graph node. Group attributes are stored as scalar
        attributes of the node, Zarr arrays are stored as array-valued
        attributes, and nested groups become directed edges representing
        object-valued LinkML attributes.

        The resulting graph provides a serialization-independent
        representation of the model that can subsequently be deserialized
        into instantiated LinkML objects.

        Parameters
        ----------
        source
            Path to the root of the Zarr store.
        schemaview
            SchemaView describing the LinkML schema.
        root_class
            Name of the LinkML root class represented by the root Zarr
            group.

        Returns
        -------
        ObjectGraph
            Graph representation of the LinkML model stored in the Zarr
            hierarchy.

        Raises
        ------
        ValueError
            If ``root_class`` is not defined in the schema or if ``source``
            does not contain a Zarr group.
        """
        graph = cls()

        z = zarr.open(source, mode="r")
        schema_class = schemaview.get_class(root_class)

        if not schema_class:
            raise ValueError(f"Root class {root_class} not found in schema.")

        if not isinstance(z, zarr.Group):
            raise ValueError(f"Source should be a zarr group, but got type {type(z)}")

        root = graph._discover_zarr_group(
            group=z,
            class_definition=schema_class,
            schemaview=schemaview,
        )
        graph.root = root.key

        return graph

    @classmethod
    def from_yaml(
        cls, source: str | Path, schemaview: SchemaView, root_class: str, resolve_arrays=False
    ) -> "ObjectGraph":
        """Construct an ObjectGraph from a YAML representation of a LinkML model.

        Parses a YAML document describing a LinkML model and constructs a
        graph representation in which each nested LinkML class instance
        becomes a graph node. Scalar attributes are stored directly on the
        node, object-valued attributes become directed graph edges, and
        array-valued attributes are either read directly from the YAML
        document or resolved from external array files.

        The resulting graph provides a serialization-independent
        representation of the model that can subsequently be deserialized
        into instantiated LinkML objects.

        Parameters
        ----------
        source
            YAML document or path to a YAML file.
        schemaview
            SchemaView describing the LinkML schema.
        root_class
            Name of the LinkML root class represented by the YAML document.
        resolve_arrays
            Whether array-valued attributes should be resolved from external
            files referenced by the YAML document. If ``False``, array values
            are read directly from the YAML document.

        Returns
        -------
        ObjectGraph
            Graph representation of the LinkML model described by the YAML
            document.

        Raises
        ------
        ValueError
            If ``source`` is not a string or path, or if ``root_class`` is
            not defined in the schema.
        """
        graph = cls()

        if isinstance(source, Path):
            with source.open() as f:
                data = yaml.safe_load(f)
            base_path = source.parent
        elif isinstance(source, str):
            if "\n" in source:
                data = yaml.safe_load(source)
                base_path = Path(".")
            else:
                source_path = Path(source)

                if source_path.exists():
                    with source_path.open() as f:
                        data = yaml.safe_load(f)
                    base_path = source_path.parent
                else:
                    data = yaml.safe_load(source)
                    base_path = Path(".")
        else:
            raise ValueError(f"Source should be of type Path or str, got {type(source)}")

        schema_class = schemaview.get_class(root_class)

        if not schema_class:
            raise ValueError(f"Root class {root_class} not found in schema.")

        root = graph._discover_yaml_dict(
            input_dict=data,
            class_definition=schema_class,
            schemaview=schemaview,
            base_path=base_path,
            resolve_arrays=resolve_arrays,
        )

        graph.root = root.key

        return graph

    @classmethod
    def from_xarray(
        cls,
        source: DataTree,
        schemaview: SchemaView,
        root_class: str,
    ) -> "ObjectGraph":
        """Construct an ObjectGraph from an xarray DataTree representation of a LinkML model.

        Traverses an xarray DataTree and constructs a graph representation in
        which each nested LinkML class instance becomes a graph node. Dataset
        attributes and array values are stored directly on nodes, while nested
        class-valued attributes become directed graph edges.

        The LinkML schema is used to determine how DataTree nodes, variables,
        coordinates, and attributes map to classes and slots in the graph.

        Parameters
        ----------
        source
            DataTree containing the serialized LinkML model.
        schemaview
            SchemaView describing the LinkML schema.
        root_class
            Name of the LinkML root class represented by the DataTree.

        Returns
        -------
        ObjectGraph
            Graph representation of the LinkML model described by the DataTree.

        Raises
        ------
        ValueError
            If `root_class` is not defined in the schema.
        """
        graph = cls()

        schema_class = schemaview.get_class(root_class)

        if not schema_class:
            raise ValueError(f"Root class {root_class} not found in schema.")

        root = graph._discover_xarray_node(
            tree=source,
            class_definition=schema_class,
            schemaview=schemaview,
        )

        graph.root = root.key
        return graph

    def __contains__(self, obj: BaseModel | UUID) -> bool:
        """Return whether a node exists in the graph.

        Parameters
        ----------
        obj
            Either the UUID of a graph node or an instantiated LinkML object.

        Returns
        -------
        bool
            ``True`` if the corresponding node exists in the graph,
            otherwise ``False``.
        """
        if isinstance(obj, UUID):
            return obj in self.nodes

        return id(obj) in self._object_index

    def __getitem__(self, obj: BaseModel | UUID):
        """Return the graph node corresponding to an object or node key.

        Parameters
        ----------
        obj
            Either the UUID of a graph node or an instantiated LinkML object.

        Returns
        -------
        GraphNode
            The corresponding graph node.

        Raises
        ------
        KeyError
            If the requested node does not exist in the graph.
        """
        if isinstance(obj, UUID):
            return self.nodes[obj]

        return self.nodes[self._object_index[id(obj)]]

    def __iter__(self) -> Iterator[GraphNode]:
        """Iterate over the graph nodes.

        Returns
        -------
        Iterator[GraphNode]
            Iterator over the graph nodes in insertion order.
        """
        return iter(self.nodes.values())

    def by_identifier(self, identifier: str) -> GraphNode:
        """Return the graph node with the given LinkML identifier.

        Parameters
        ----------
        identifier
            Value of the LinkML identifier slot.

        Returns
        -------
        GraphNode
            Node corresponding to the specified LinkML identifier.

        Raises
        ------
        KeyError
            If no node with the given identifier exists in the graph.
        """
        return self.nodes[self._identifier_index[identifier]]

    def _discover_zarr_group(
        self,
        group: zarr.Group,
        class_definition,
        schemaview: SchemaView,
    ) -> GraphNode:
        """Recursively construct graph nodes from a Zarr group hierarchy.

        Traverses a Zarr group representing a LinkML object and constructs
        the corresponding graph node. Group attributes are stored as scalar
        attributes of the node, Zarr arrays become array-valued attributes,
        and nested groups are recursively converted into child nodes
        connected by graph edges representing object-valued LinkML
        attributes.

        Parameters
        ----------
        group
            Zarr group corresponding to a LinkML class instance.
        class_definition
            LinkML class definition describing the structure of the current
            group.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        GraphNode
            Graph node corresponding to the supplied Zarr group.

        Raises
        ------
        ValueError
            If a nested object is not stored as a Zarr group or if the range
            of an object-valued attribute cannot be resolved to a LinkML
            class.
        """
        node = GraphNode(
            class_name=class_definition.name,
        )

        for name, value in group.attrs.items():
            node.values[name] = value

        self.nodes[node.key] = node

        for name, value in group.members():
            slot = schemaview.induced_slot(
                name,
                class_definition.name,
            )

            if slot.array:
                node.values[name] = value[()]
                continue

            child_class = schemaview.get_class(slot.range)
            if not isinstance(value, zarr.Group):
                raise ValueError(
                    f"The value of {name} in group.members is expected to "
                    f"be a zarr Group, got {type(value)}."
                )

            if not child_class:
                raise ValueError(f"Root class {child_class} not found in schema.")

            child = self._discover_zarr_group(
                group=value,
                class_definition=child_class,
                schemaview=schemaview,
            )

            edge = GraphEdge(
                parent=node.key,
                child=child.key,
                slot_name=str(slot.name),
                multivalued=bool(slot.multivalued),
                inlined=bool(slot.inlined),
            )

            node.outgoing.append(edge)
            child.incoming.append(edge)

        return node

    def _discover_hdf5_group(
        self,
        group: h5py.Group,
        class_definition: ClassDefinition,
        schemaview: SchemaView,
    ) -> GraphNode:
        """Recursively construct graph nodes from an HDF5 group hierarchy.

        Traverses an HDF5 group representing a LinkML object and constructs
        the corresponding graph node. Group attributes are stored as scalar
        attributes of the node, datasets become array-valued attributes, and
        nested groups are recursively converted into child nodes connected
        by graph edges representing object-valued LinkML attributes.

        Parameters
        ----------
        group
            HDF5 group corresponding to a LinkML class instance.
        class_definition
            LinkML class definition describing the structure of the current
            group.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        GraphNode
            Graph node corresponding to the supplied HDF5 group.

        Raises
        ------
        ValueError
            If the range of an object-valued attribute cannot be resolved to
            a LinkML class.
        """
        node = GraphNode(
            class_name=class_definition.name,
        )

        for name, value in group.attrs.items():
            node.values[name] = value

        self.nodes[node.key] = node

        for name, value in group.items():
            slot = schemaview.induced_slot(
                name,
                class_definition.name,
            )

            if slot.array:
                node.values[name] = value[()]
                continue

            child_class = schemaview.get_class(slot.range)

            if not child_class:
                raise ValueError(f"Root class {child_class} not found in schema.")

            child = self._discover_hdf5_group(
                group=value,
                class_definition=child_class,
                schemaview=schemaview,
            )

            edge = GraphEdge(
                parent=node.key,
                child=child.key,
                slot_name=str(slot.name),
                multivalued=bool(slot.multivalued),
                inlined=bool(slot.inlined),
            )

            node.outgoing.append(edge)
            child.incoming.append(edge)

        return node

    def _discover_xarray_node(
        self,
        tree: DataTree,
        class_definition: ClassDefinition,
        schemaview: SchemaView,
    ) -> GraphNode:
        node = GraphNode(
            class_name=class_definition.name,
        )
        self.nodes[node.key] = node
        for name, value in tree.attrs.items():
            node.values[str(name)] = value

        dataset = tree.to_dataset()

        for name in dict.fromkeys([*dataset.coords, *dataset.data_vars]):
            array = dataset[name]

            slot = schemaview.induced_slot(
                name,
                class_definition.name,
            )

            child_class = schemaview.get_class(slot.range)
            if child_class is None:
                raise ValueError(
                    f"Slot '{name}' on {class_definition.name} " "does not have a class range."
                )

            child = self._discover_xarray_array(
                array=array,
                class_definition=child_class,
                schemaview=schemaview,
            )
            edge = GraphEdge(
                parent=node.key,
                child=child.key,
                slot_name=str(slot.name),
                multivalued=bool(slot.multivalued),
                inlined=bool(slot.inlined),
            )

            node.outgoing.append(edge)
            child.incoming.append(edge)

        for name, child_tree in tree.children.items():
            slot = schemaview.induced_slot(
                name,
                class_definition.name,
            )

            child_class = schemaview.get_class(slot.range)

            if child_class is None:
                raise ValueError(
                    f"Expected slot '{name}' on " f"{class_definition.name} to have a class range."
                )

            child = self._discover_xarray_node(
                tree=child_tree,
                class_definition=child_class,
                schemaview=schemaview,
            )
            edge = GraphEdge(
                parent=node.key,
                child=child.key,
                slot_name=str(slot.name),
                multivalued=bool(slot.multivalued),
                inlined=bool(slot.inlined),
            )

            node.outgoing.append(edge)
            child.incoming.append(edge)
        return node

    def _discover_xarray_array(
        self,
        array: xr.DataArray,
        class_definition: ClassDefinition,
        schemaview: SchemaView,
    ) -> GraphNode:
        node = GraphNode(
            class_name=class_definition.name,
        )

        self.nodes[node.key] = node
        array_slot = None

        for slot_name in schemaview.class_slots(class_definition.name):
            slot = schemaview.induced_slot(
                slot_name,
                class_definition.name,
            )
            if slot.array:
                array_slot = slot
                break

        if array_slot is None:
            raise ValueError(f"{class_definition.name} has no array-valued slot.")

        node.values[str(array_slot.name)] = array.values

        for name, value in array.attrs.items():
            node.values[str(name)] = value
        return node

    def _discover_yaml_dict(
        self,
        input_dict: dict,
        class_definition: ClassDefinition,
        schemaview: SchemaView,
        base_path: Path,
        resolve_arrays: bool,
    ) -> GraphNode:
        """Recursively construct graph nodes from a YAML representation.

        Traverses a YAML mapping representing a LinkML object and constructs
        the corresponding graph node. Scalar attributes are stored directly
        on the node, object-valued attributes are recursively converted into
        child nodes connected by graph edges, and array-valued attributes are
        either read directly from the YAML document or resolved from
        externally stored array files.

        Parameters
        ----------
        input_dict
            YAML mapping corresponding to a LinkML class instance.
        class_definition
            LinkML class definition describing the expected structure of the
            mapping.
        schemaview
            SchemaView describing the LinkML schema.
        base_path
            Directory relative to which external array file paths are
            resolved.
        resolve_arrays
            Whether array-valued attributes should be resolved from external
            files referenced by the YAML document. If ``False``, the values
            from the YAML document are stored directly.

        Returns
        -------
        GraphNode
            Graph node corresponding to the supplied YAML mapping.

        Raises
        ------
        ValueError
            If an array reference is missing its source, format, or file, if
            an unsupported array format is encountered, or if the range of an
            object-valued attribute cannot be resolved to a LinkML class.
        NotImplementedError
            If multiple array sources are specified for a single
            array-valued attribute.
        """
        node = GraphNode(
            class_name=class_definition.name,
        )

        self.nodes[node.key] = node

        for name, value in input_dict.items():

            slot = schemaview.induced_slot(
                name,
                class_definition.name,
            )

            if slot.array:
                if not resolve_arrays:
                    node.values[name] = value
                    continue

                sources = value.get("source")
                if sources is None:
                    raise ValueError(f"Array slot '{name}' has no source.")

                if len(sources) != 1:
                    raise NotImplementedError("Multiple array sources are not yet supported.")

                source = sources[0]
                fmt = source.get("format")
                file = source.get("file")

                if fmt is None:
                    raise ValueError(f"Array slot '{name}' has no format.")

                if file is None:
                    raise ValueError(f"Array slot '{name}' has no file.")

                file = base_path / file

                if fmt == "numpy":
                    node.values[name] = np.load(file)
                elif fmt == "hdf5":
                    with h5py.File(file, "r") as f:
                        node.values[name] = f["data"][()]
                elif fmt == "zarr":
                    z = zarr.open(file, mode="r")
                    node.values[name] = z["data"][()]
                elif fmt == "xarray_netcdf":
                    data_array = xr.open_dataarray(
                        file,
                        engine="h5netcdf",
                    )
                    node.values[name] = data_array.values
                elif fmt == "xarray_zarr":
                    data_array = xr.open_dataarray(
                        file,
                        engine="zarr",
                    )
                    node.values[name] = data_array.values
                else:
                    raise ValueError(f"Unsupported array format '{fmt}'.")
                continue

            if isinstance(value, dict):
                child_class = schemaview.get_class(
                    slot.range,
                )

                if not child_class:
                    raise ValueError(f"Root class {child_class} not found in schema.")

                child = self._discover_yaml_dict(
                    input_dict=value,
                    class_definition=child_class,
                    schemaview=schemaview,
                    base_path=base_path,
                    resolve_arrays=resolve_arrays,
                )

                edge = GraphEdge(
                    parent=node.key,
                    child=child.key,
                    slot_name=str(slot.name),
                    multivalued=bool(slot.multivalued),
                    inlined=bool(slot.inlined),
                )

                node.outgoing.append(edge)
                child.incoming.append(edge)
                continue

            node.values[name] = value
        return node

    def _discover(
        self,
        obj: BaseModel,
        schemaview: SchemaView,
    ) -> GraphNode:
        """Recursively construct graph nodes from an instantiated LinkML model.

        Traverses an instantiated LinkML object and constructs the
        corresponding graph node. Scalar and array-valued attributes remain
        associated with the node, while object-valued attributes are
        recursively discovered and represented as graph edges. Previously
        visited objects are reused to preserve object identity and avoid
        duplicate nodes.

        Parameters
        ----------
        obj
            Instantiated LinkML object to add to the graph.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        GraphNode
            Graph node corresponding to the supplied LinkML object.
        """
        obj_id = id(obj)

        if obj_id in self._object_index:
            return self.nodes[self._object_index[obj_id]]

        class_name = type(obj).__name__
        cls = schemaview.get_class(class_name)
        identifier = None

        if cls is not None:
            id_slot = schemaview.get_identifier_slot(cls.name)
            if id_slot is not None:
                identifier = getattr(obj, id_slot.name)

        node = GraphNode(
            obj=obj,
            class_name=class_name,
            identifier=identifier,
        )

        self.nodes[node.key] = node
        self._object_index[obj_id] = node.key

        if identifier is not None:
            self._identifier_index[identifier] = node.key

        for slot_name, value in vars(obj).items():
            slot = schemaview.induced_slot(
                slot_name,
                class_name,
            )

            self._discover_value(
                value=value,
                parent=node,
                slot=slot,
                schemaview=schemaview,
            )

        return node

    def _set_value(
        self,
        node: GraphNode,
        name: str,
        value: Any,
        slot,
    ) -> None:
        name = str(name)
        node.values[name] = value

        if slot.array is not None:
            dimensions = tuple(
                str(dimension.alias)
                for dimension in slot.array.dimensions or []
                if dimension.alias is not None
            )
        else:
            dimensions = None

        node.value_metadata[name] = GraphValueMetadata(
            dimensions=dimensions,
        )

    def _discover_value(
        self,
        value: Any,
        parent: GraphNode,
        slot,
        schemaview: SchemaView,
    ):
        """Discover object-valued attributes within a LinkML attribute value.

        Traverses the value of a LinkML attribute and adds any referenced
        LinkML objects to the graph. Object-valued attributes become graph
        edges connecting the parent node to the referenced child nodes,
        preserving the multiplicity and inlining semantics defined by the
        LinkML schema.

        Scalar and array-valued attributes are ignored, as they remain
        stored directly on their corresponding graph node.

        Parameters
        ----------
        value
            Value of the LinkML attribute to inspect.
        parent
            Graph node corresponding to the object that owns the attribute.
        slot
            LinkML slot definition describing the attribute.
        schemaview
            SchemaView describing the LinkML schema.
        """
        name = str(slot.name)
        child_class = schemaview.get_class(slot.range)

        if slot.array or child_class is None or value is None:
            self._set_value(
                node=parent,
                name=name,
                value=value,
                slot=slot,
            )
            return

        if isinstance(value, BaseModel):
            self._add_child(
                parent=parent,
                child_obj=value,
                slot=slot,
                schemaview=schemaview,
                multivalued=False,
            )
            return

        values: Iterable[Any] | list[Any] | tuple[Any, ...] | set[Any]
        if isinstance(value, dict):
            values = value.values()
        elif isinstance(value, (list, tuple, set)):
            values = value
        else:
            parent.values[name] = value
            return

        for child_obj in values:
            self._add_child(
                parent=parent,
                child_obj=child_obj,
                slot=slot,
                schemaview=schemaview,
                multivalued=True,
            )

    def _add_child(
        self,
        parent: GraphNode,
        child_obj: BaseModel,
        slot,
        schemaview: SchemaView,
        multivalued: bool,
    ) -> None:
        child = self._discover(child_obj, schemaview)

        edge = GraphEdge(
            parent=parent.key,
            child=child.key,
            slot_name=str(slot.name),
            multivalued=multivalued,
            inlined=bool(slot.inlined),
        )

        parent.outgoing.append(edge)
        child.incoming.append(edge)

    def dependency_order(self) -> Iterator[GraphNode]:
        """Iterate over graph nodes in dependency order.

        Returns graph nodes in a topological order such that every referenced
        LinkML object is yielded before any object that references it. This
        ordering is suitable for reconstructing an instantiated LinkML model
        from an ObjectGraph, ensuring that object-valued attributes can be
        assigned after their referenced objects have been constructed.

        Yields
        ------
        GraphNode
            Graph nodes in dependency order.
        """
        ts: TopologicalSorter[UUID] = TopologicalSorter()

        for node in self.nodes.values():
            ts.add(
                node.key,
                *(edge.child for edge in node.outgoing),
            )

        for key in ts.static_order():
            yield self.nodes[key]

    def hierarchy_order(self) -> Iterator[GraphNode]:
        """Iterate over graph nodes in hierarchy order.

        Traverses the ObjectGraph starting from the root node using a
        depth-first traversal, yielding each node exactly once. Shared
        references are visited only on their first encounter to avoid
        revisiting the same LinkML object.

        This ordering is suitable for serializing the graph to hierarchical
        storage formats such as YAML, HDF5, and Zarr, where object-valued
        attributes are represented by nested structures.

        Yields
        ------
        GraphNode
            Graph nodes in depth-first hierarchy order beginning at the root
            node.
        """
        if self.root is None:
            return

        visited: set[UUID] = set()

        def visit(key: UUID):
            """Recursively visit nodes in depth-first hierarchy order.

            Parameters
            ----------
            key
                Key of the graph node to visit.

            Yields
            ------
            GraphNode
                The node identified by ``key`` followed by each of its
                descendants, skipping nodes that have already been visited.
            """
            if key in visited:
                return

            visited.add(key)

            node = self.nodes[key]
            yield node

            for edge in node.outgoing:
                yield from visit(edge.child)

        yield from visit(self.root)
