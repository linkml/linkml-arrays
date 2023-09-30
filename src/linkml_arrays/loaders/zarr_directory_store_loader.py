from typing import Type, Union

import zarr
from pydantic import BaseModel

from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition


def iterate_element(group: zarr.hierarchy.Group, element_type: ClassDefinition, schemaview: SchemaView) -> dict:
    ret_dict = dict()
    for k, v in group.attrs.items():
        ret_dict[k] = v

    for k, v in group.items():
        found_slot = schemaview.induced_slot(k, element_type.name)  # assumes the slot name has been written as the name which is OK for now.
        if "linkml:elements" in found_slot.implements:
            assert isinstance(v, zarr.Array)
            v = v[()]  # read all the values into memory
        elif isinstance(v, zarr.hierarchy.Group):  # it's a subgroup
            found_slot_range = schemaview.get_class(found_slot.range)
            v = iterate_element(v, found_slot_range, schemaview)
        # else: do not transform v
        ret_dict[k] = v

    return ret_dict


class ZarrDirectoryStoreLoader(Loader):

    def load_any(self, source: str, **kwargs):
        """ Return element formatted as a YAML string with the path to a Zarr directory store"""
        return self.load(source, **kwargs)

    def loads(self, source: str, **kwargs):
        """ Return element formatted as a YAML string with the path to a Zarr directory store"""
        return self.load(source, **kwargs)

    def load(self, source: str, target_class: Type[Union[YAMLRoot, BaseModel]], schemaview: SchemaView, **kwargs):
        """ Return element formatted as a YAML string with the path to a Zarr directory store"""
        element_type = schemaview.get_class(target_class.__name__)
        z = zarr.open(source, mode="r")
        element = iterate_element(z, element_type, schemaview)
        obj = target_class(**element)

        return obj


