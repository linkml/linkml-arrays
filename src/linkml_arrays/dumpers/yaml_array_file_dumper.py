"""Base class for dumping a LinkML model to YAML with paths to files containing arrays."""

import os
from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    element: Union[YAMLRoot, BaseModel],
    schemaview: SchemaView,
    output_dir: Path,
    write_array: Callable,
    format: str,
    parent_identifier=None,
    inlined_name=None,
):
    """Recursively iterate through the elements of a LinkML model and save them.

    Return a dictionary with the same structure as the input element, but where the slots
    with the "array" element are written to an array file and the paths to these
    files are returned in the dictionary. The paths are relative to the output directory.

    Raises:
        ValueError: If the class requires an identifier and it is not provided.
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
        if found_slot.array:
            if id_slot is None and parent_identifier is None:
                raise ValueError("The class requires an identifier.")

            # determine the output file name without the suffix
            if id_slot is not None:
                output_file_name = f"{id_value}.{found_slot.name}"
            elif inlined_name is not None:
                output_file_name = f"{parent_identifier}.{inlined_name}.{found_slot.name}"
            elif parent_identifier is not None:
                output_file_name = f"{parent_identifier}.{found_slot.name}"
            else:
                output_file_name = f"{found_slot.name}"

            # if output_dir is absolute, make it relative to current working directory
            # and create the directory if it does not exist
            if output_dir.is_absolute():
                output_dir = Path(os.path.relpath(output_dir, start=os.getcwd()))
            output_dir.mkdir(exist_ok=True)
            output_file_path_no_suffix = output_dir / output_file_name

            # save the numpy array to file and write the file path to the dictionary
            output_file_path = write_array(v, output_file_path_no_suffix)
            ret_dict[k] = {
                "source": [
                    {
                        "file": f"./{output_file_path}",
                        "format": format,
                    }
                ]
            }
        else:
            if isinstance(v, BaseModel):
                v2 = _iterate_element(
                    v,
                    schemaview,
                    output_dir,
                    write_array,
                    format,
                    id_value,
                    inlined_name=found_slot.name,
                )
                ret_dict[k] = v2
            else:
                ret_dict[k] = v
    return ret_dict


class YamlArrayFileDumper(Dumper, metaclass=ABCMeta):
    """Base dumper class for LinkML models to YAML files with paths to array files."""

    # FORMAT is a class attribute that must be set by subclasses

    def dumps(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> str:
        """Return element formatted as a YAML string."""
        if output_dir is None:
            output_dir = "."
        input = _iterate_element(
            element, schemaview, Path(output_dir), self.write_array, self.FORMAT
        )

        return yaml.dump(input)

    @classmethod
    @abstractmethod
    def write_array(cls, array: Union[List, np.ndarray], output_file_path: Union[str, Path]):
        """Write an array to a file."""
        raise NotImplementedError("Subclasses must implement this method.")
