"""Base class for dumping a LinkML model to YAML with paths to files containing arrays."""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_arrays.graph_utils.graph import ObjectGraph
from linkml_arrays.graph_utils.serializers import YAMLGraphArraySerializer


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
        output_dir = Path(output_dir or ".")

        graph = ObjectGraph.from_root(element, schemaview)

        serializer = YAMLGraphArraySerializer(
            graph=graph,
            output_dir=output_dir,
            write_array=self.write_array,
            array_format=self.FORMAT,
        )

        return yaml.dump(serializer.serialize())

    @classmethod
    @abstractmethod
    def write_array(cls, array: Union[List, np.ndarray], output_file_path: Union[str, Path]):
        """Write an array to a file."""
        raise NotImplementedError("Subclasses must implement this method.")
