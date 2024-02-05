"""Class for loading a LinkML model from a YAML file with NumPy file paths."""

from typing import Type, Union

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

    Datasets are read into memory."""
    ret_dict = dict()
    for k, v in input_dict.items():
        found_slot = schemaview.induced_slot(k, element_type.name)
        if "linkml:elements" in found_slot.implements:
            array_file_path = v.replace("file:./", "")
            v = np.load(array_file_path)  # TODO: support lazy loading
        elif isinstance(v, dict):
            found_slot_range = schemaview.get_class(found_slot.range)
            v = _iterate_element(v, found_slot_range, schemaview)
        # else: do not transform v
        ret_dict[k] = v

    return ret_dict


class YamlNumpyLoader(Loader):
    """Class for loading a LinkML model from a YAML file with NumPy file paths."""

    def load_any(self, source: str, **kwargs):
        """Create an instance of the target class from a YAML file with NumPy file paths."""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """Create an instance of the target class from a YAML file with NumPy file paths."""
        return self.load(source, **kwargs)

    def load(
        self,
        source: str,
        target_class: Type[Union[YAMLRoot, BaseModel]],
        schemaview: SchemaView,
        **kwargs,
    ):
        """Create an instance of the target class from a YAML file with NumPy file paths."""
        input_dict = yaml.safe_load(source)

        element_type = schemaview.get_class(target_class.__name__)
        element = _iterate_element(input_dict, element_type, schemaview)
        obj = target_class(**element)

        return obj
