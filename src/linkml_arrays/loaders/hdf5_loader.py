"""Class for loading a LinkML model from an HDF5 file."""

from typing import Type, Union

import h5py
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition
from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    group: h5py.Group, element_type: ClassDefinition, schemaview: SchemaView
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
        if found_slot.array:
            assert isinstance(v, h5py.Dataset)
            v = v[()]  # read all the values into memory TODO: support lazy loading
        elif isinstance(v, h5py.Group):  # it's a subgroup
            found_slot_range = schemaview.get_class(found_slot.range)
            v = _iterate_element(v, found_slot_range, schemaview)
        # else: do not transform v
        ret_dict[k] = v

    return ret_dict


class Hdf5Loader(Loader):
    """Class for loading a LinkML model from an HDF5 file."""

    def load_any(self, source: str, **kwargs):
        """Create an instance of the target class from an HDF5 file."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Create an instance of the target class from an HDF5 file."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Create an instance of the target class from an HDF5 file."""
        element_type = schemaview.get_class(target_class.__name__)
        with h5py.File(source, "r") as f:
            element = _iterate_element(f, element_type, schemaview)
        obj = target_class(**element)

        return obj
