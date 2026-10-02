"""Classes for loading a LinkML model from an xarray zarr or netcdf file."""

from pathlib import Path
from typing import Type, Union

from linkml_runtime import SchemaView
from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel
from xarray import open_datatree

from linkml_arrays.graph_utils.deserializers import GraphDeserializer
from linkml_arrays.graph_utils.graph import ObjectGraph


class XarrayZarrLoader(Loader):
    """Loader class for LinkML models from xarray zarr stores."""

    def load_any(self, source: str, **kwargs):
        """Load a LinkML model from an xarray zarr store."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Load a LinkML model from an xarray zarr store."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Load a LinkML model from an xarray zarr store.

        The zarr store is opened as an xarray DataTree and converted to an
        ObjectGraph before being deserialized into the target class.

        Parameters
        ----------
        source
            Path to the zarr store.
        target_class
            LinkML class to deserialize the graph into.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        YAMLRoot or BaseModel
            Deserialized LinkML model.
        """
        tree = open_datatree(
            Path(source),
            engine="zarr",
        )

        graph = ObjectGraph.from_xarray(
            source=tree,
            schemaview=schemaview,
            root_class=target_class.__name__,
        )

        return GraphDeserializer.from_target_class(
            graph=graph,
            schemaview=schemaview,
            target_class=target_class,
        ).deserialize(target_class)


class XarrayNetCDFLoader(Loader):
    """Loader class for LinkML models from xarray netcdf files."""

    def load_any(self, source: str, **kwargs):
        """Load a LinkML model from an xarray netcdf file."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Load a LinkML model from an xarray netcdf file."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Load a LinkML model from an xarray netcdf file.

        The netcdf file is opened as an xarray DataTree and converted to an
        ObjectGraph before being deserialized into the target class.

        Parameters
        ----------
        source
            Path to the netcdf file.
        target_class
            LinkML class to deserialize the graph into.
        schemaview
            SchemaView describing the LinkML schema.

        Returns
        -------
        YAMLRoot or BaseModel
            Deserialized LinkML model.
        """
        tree = open_datatree(
            Path(source),
            engine="h5netcdf",
        )

        graph = ObjectGraph.from_xarray(
            source=tree,
            schemaview=schemaview,
            root_class=target_class.__name__,
        )

        return GraphDeserializer.from_target_class(
            graph=graph,
            schemaview=schemaview,
            target_class=target_class,
        ).deserialize(target_class)
