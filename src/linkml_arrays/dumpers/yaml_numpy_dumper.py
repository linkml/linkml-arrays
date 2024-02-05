"""Class for dumpling a LinkML model to a YAML file with paths to NumPy files."""

from typing import Union

import numpy as np
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, parent_identifier=None
):
    """Recursively iterate through the elements of a LinkML model and save them.

    Returns a dictionary with the same structure as the input element, but with the slots
    that implement "linkml:elements" (arrays) are written to HDF5 files and the paths to these
    files are returned in the dictionary. Each array is written to an HDF5 dataset at path
    "/data" in a new HDF5 file.
    """
    # get the type of the element
    element_type = type(element).__name__

    # ask schemaview whether it has a class by this name
    found_class = schemaview.get_class(element_type)

    id_slot = schemaview.get_identifier_slot(found_class.name)
    if id_slot is not None:
        id_value = getattr(element, id_slot.name)
    else:
        id_value = None

    ret_dict = dict()
    for k, v in vars(element).items():
        found_slot = schemaview.induced_slot(k, element_type)
        if "linkml:elements" in found_slot.implements:
            if id_slot is None and parent_identifier is None:
                raise ValueError("The class requires an identifier.")
            # save the numpy array to file
            if parent_identifier is not None:
                output_file_path = f"{parent_identifier}.{found_class.name}.{found_slot.name}.npy"
            else:
                output_file_path = f"{found_class.name}.{found_slot.name}.npy"
            np.save(output_file_path, v)  # TODO do not assume that there is only one by this name
            ret_dict[k] = f"file:./{output_file_path}"  # TODO make this nicer
        else:
            if isinstance(v, BaseModel):
                v2 = _iterate_element(v, schemaview, id_value)
                ret_dict[k] = v2
            else:
                ret_dict[k] = v
    return ret_dict


class YamlNumpyDumper(Dumper):
    """Dumper class for LinkML models to YAML files with paths to NumPy files."""

    def dumps(self, element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, **kwargs) -> str:
        """Return element formatted as a YAML string."""
        input = _iterate_element(element, schemaview)

        return yaml.dump(input)
