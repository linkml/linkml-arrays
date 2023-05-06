from decimal import Decimal

from typing import Union

import numpy as np
from pydantic import BaseModel
import yaml

from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.formatutils import remove_empty_items
from linkml_runtime.utils.yamlutils import YAMLRoot


def numpy_representer(dumper, data):
        print(data)
        return dumper.represent_scalar(u'!array', u'put path to numpy file here')


class YAMLNumpyDumper(Dumper):

    def dumps(self, element: Union[YAMLRoot, BaseModel], **kwargs) -> str:
        """ Return element formatted as a YAML string with paths to numpy files containing the ndarrays"""
        input = element.dict()
        safe_dumper = yaml.SafeDumper
        safe_dumper.add_representer(np.ndarray, numpy_representer)
        return yaml.dump(input,
                         Dumper=safe_dumper, sort_keys=False,
                         allow_unicode=True,
                         **kwargs)






