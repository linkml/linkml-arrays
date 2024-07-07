"""Class for loading a LinkML model from a YAML file with arrays at supported file paths."""

from typing import Type, Union

import h5py
import numpy as np
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition
from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    input_dict: dict, element_type: ClassDefinition, schemaview: SchemaView
) -> dict:
    """Recursively iterate through the elements of a LinkML model and load them into a dict.

    Datasets are read into memory.

    Raises:
        ValueError: If the array slot has no source or format, or if the format is not supported.
    """
    ret_dict = dict()
    for k, v in input_dict.items():
        found_slot = schemaview.induced_slot(k, element_type.name)
        if found_slot.array:
            sources = v.get("source", None)
            if sources is None:
                raise ValueError(f"Array slot {k} has no source.")
            for source in sources:
                format = source.get("format", None)
                if format is None:
                    raise ValueError(f"Array slot {k}, source {source} has no format.")
                if format == "hdf5":
                    file = source.get("file", None)
                    if file is None:
                        raise ValueError(
                            f"Array slot {k}, source {source}, format {format} has no file."
                        )
                    array_file_path = file
                    with h5py.File(array_file_path, "r") as f:
                        # read all the values into memory TODO: support lazy loading
                        v = f["data"][()]
                elif format == "numpy":
                    file = source.get("file", None)
                    if file is None:
                        raise ValueError(
                            f"Array slot {k}, source {source}, format {format} has no file."
                        )
                    array_file_path = file
                    # read all the values into memory TODO: support lazy loading
                    v = np.load(array_file_path)
        elif isinstance(v, dict):
            found_slot_range = schemaview.get_class(found_slot.range)
            v = _iterate_element(v, found_slot_range, schemaview)
        # else: do not transform v
        ret_dict[k] = v

    return ret_dict


class YamlArrayFileLoader(Loader):
    """Class for loading a model from a YAML file with arrays at supported file paths."""

    def load_any(self, source: str, **kwargs):
        """Create an instance of the target class from a YAML file with arrays in files."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Create an instance of the target class from a YAML file with arrays in files."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Create an instance of the target class from a YAML file with arrays in files."""
        input_dict = yaml.safe_load(source)

        element_type = schemaview.get_class(target_class.__name__)
        element = _iterate_element(input_dict, element_type, schemaview)
        obj = target_class(**element)

        return obj
