"""Class for dumping a LinkML model to an HDF5 file."""

from pathlib import Path
from typing import Union

import h5py
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, group: h5py.Group = None
):
    """Recursively iterate through the elements of a LinkML model and save them.

    Write Pydantic BaseModel objects as groups, slots with the "array" element
    as datasets, and other slots as attributes.
    """
    # get the type of the element
    element_type = type(element).__name__

    for k, v in vars(element).items():
        found_slot = schemaview.induced_slot(k, element_type)
        if found_slot.array:
            # save the numpy array to an hdf5 dataset
            group.create_dataset(found_slot.name, data=v)
        else:
            if isinstance(v, BaseModel):
                # create a subgroup and recurse
                subgroup = group.create_group(k)
                _iterate_element(v, schemaview, subgroup)
            else:
                # create an attribute on the group
                group.attrs[k] = v


class Hdf5Dumper(Dumper):
    """Dumper class for LinkML models to HDF5 files."""

    # TODO is this the right method to overwrite? it does not dump a string
    def dumps(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        output_file_path: Union[str, Path],
        **kwargs,
    ):
        """Dump the element to an HDF5 file."""
        with h5py.File(output_file_path, "w") as f:
            _iterate_element(element, schemaview, f)
