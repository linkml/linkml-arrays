"""Class for dumping a LinkML model to an HDF5 file."""

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

    Writes Pydantic BaseModel objects as groups, slots that implement "linkml:elements"
    as datasets, and other slots as attributes.
    """
    # get the type of the element
    element_type = type(element).__name__

    for k, v in vars(element).items():
        found_slot = schemaview.induced_slot(k, element_type)
        if "linkml:elements" in found_slot.implements:
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

    return


class Hdf5Dumper(Dumper):
    """Dumper class for LinkML models to HDF5 files."""

    def dumps(self, element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, **kwargs) -> str:
        """Dump the element to an HDF5 file.

        Raises:
            ValueError: If the class requires an identifier and it is not provided.
        """
        id_slot = schemaview.get_identifier_slot(element.__class__.__name__)
        if id_slot is None:
            raise ValueError("The class requires an identifier.")
        id_value = getattr(element, id_slot.name)
        output_file_path = f"{id_value}.h5"
        with h5py.File(output_file_path, "w") as f:
            _iterate_element(element, schemaview, f)
