"""Class for dumping a LinkML model to YAML."""

from typing import Union

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel


def _iterate_element(
    element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, parent_identifier=None
):
    """Recursively iterate through the elements of a LinkML model and save them.

    Returns a dictionary with the same structure as the input element, but where the slots
    with the "array" element are written as lists of lists in YAML.

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
            assert isinstance(v, list)
            ret_dict[k] = v
        else:
            if isinstance(v, BaseModel):
                v2 = _iterate_element(v, schemaview, id_value)
                ret_dict[k] = v2
            else:
                ret_dict[k] = v
    return ret_dict


class YamlDumper(Dumper):
    """Dumper class for LinkML models to YAML files."""

    def dumps(self, element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, **kwargs) -> str:
        """Return element formatted as a YAML string."""
        input = _iterate_element(element, schemaview)

        return yaml.dump(input)
