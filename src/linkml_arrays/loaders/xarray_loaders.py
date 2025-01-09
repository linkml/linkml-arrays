"""Class for loading a LinkML model from a Zarr directory store."""

from typing import Type, Union

from pathlib import Path
from xarray.backends.api import open_datatree
import xarray as xr
from xarray.core.datatree import DataTree
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition
from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    group: DataTree, element_type: ClassDefinition, schemaview: SchemaView
) -> dict:
    """Recursively iterate through the elements of a LinkML model and load them into a dict.

    Datasets are read into memory.
    """
    ret_dict = dict()
    for k, v in group.attrs.items():
        ret_dict[k] = v

    for k, v in group.items():
        found_slot = schemaview.induced_slot(
            k, element_type.name
        )  # assumes the slot name has been written as the name which is OK for now.
        if isinstance(v, xr.DataArray):
            if not v.coords:
                value_dict = {key: v.attrs[key] for key in v.attrs}
                value_dict.update({"values": v.values})   # read all the values into memory  # TODO support lazy loading
            else:
                value_dict = {key: v.attrs[key] for key in v.attrs}
                value_dict.update({"values": v.values})  # read all the values into memory  # TODO support lazy loading


                for coord in v.coords:
                    coordinate_array_dict = {key: value for key, value in v.coords[coord].attrs.items()}
                    coordinate_array_dict.update({"values": v.coords[coord].values})
                    ret_dict[coord] = coordinate_array_dict

            ret_dict[k] = value_dict

        elif isinstance(v, DataTree):  # it's a subgroup
            found_slot_range = schemaview.get_class(found_slot.range)
            v = _iterate_element(v, found_slot_range, schemaview)
            ret_dict[k] = v

    return ret_dict


class XarrayZarrLoader(Loader):
    """Class for loading a LinkML model from a xarray Zarr directory store."""

    def load_any(self, source: str, **kwargs):
        """Create an instance of the target class from a Zarr directory store."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Create an instance of the target class from a Zarr directory store."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Create an instance of the target class from a Zarr directory store."""
        element_type = schemaview.get_class(target_class.__name__)
        z = open_datatree(Path(source), engine="zarr")
        element = _iterate_element(z, element_type, schemaview)
        obj = target_class(**element)

        return obj


class XarrayNetCDFLoader(Loader):
    """Class for loading a LinkML model from a xarray netcdf store."""

    def load_any(self, source: str, **kwargs):
        """Create an instance of the target class from a netcdf store."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Create an instance of the target class from a netcdf store."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Create an instance of the target class from a netcdf store."""
        element_type = schemaview.get_class(target_class.__name__)
        # opening with this engine gives problems with permissions at least on windows.
        z = open_datatree(Path(source), engine='h5netcdf')
        element = _iterate_element(z, element_type, schemaview)
        obj = target_class(**element)

        return obj
