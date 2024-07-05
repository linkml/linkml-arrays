"""Class for dumping a LinkML model to a YAML file with paths to HDF5 files."""

import h5py
import numpy as np
from pathlib import Path
from typing import Union, List

from .yaml_array_file_dumper import YamlArrayFileDumper


class YamlHdf5Dumper(YamlArrayFileDumper):
    """Dumper class for LinkML models to YAML files with paths to NumPy files."""

    FILE_SUFFIX = ".h5"  # used in parent class

    @classmethod
    def write_array(cls, array: Union[List, np.ndarray], output_file_path_no_suffix: Union[str, Path]):
        """Write an array to a file."""
        # TODO do not assume that there is only one by this name
        # add suffix to the file name
        output_file_path = output_file_path_no_suffix.parent / (output_file_path_no_suffix.name + cls.FILE_SUFFIX)
        with h5py.File(output_file_path, "w") as f:
            f.create_dataset("data", data=array)
        return output_file_path
