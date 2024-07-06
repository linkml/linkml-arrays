"""Class for dumpling a LinkML model to a YAML file with paths to NumPy files."""

from pathlib import Path
from typing import List, Union

import numpy as np

from .yaml_array_file_dumper import YamlArrayFileDumper


class YamlNumpyDumper(YamlArrayFileDumper):
    """Dumper class for LinkML models to YAML files with paths to NumPy files."""

    FILE_SUFFIX = ".npy"  # used in parent class

    @classmethod
    def write_array(
        cls, array: Union[List, np.ndarray], output_file_path_no_suffix: Union[str, Path]
    ):
        """Write an array to a file."""
        # TODO do not assume that there is only one by this name
        # add suffix to the file name
        output_file_path = output_file_path_no_suffix.parent / (
            output_file_path_no_suffix.name + cls.FILE_SUFFIX
        )
        arr = np.array(array)
        np.save(output_file_path, arr)
        return output_file_path
