"""Class for dumping a LinkML model to YAML with paths to HDF5 files."""

from pathlib import Path
from typing import List, Union

import h5py
import numpy as np

from .yaml_array_file_dumper import YamlArrayFileDumper


class YamlHdf5Dumper(YamlArrayFileDumper):
    """Dumper class for LinkML models to YAML with paths to HDF5 files, one per array.

    Each array is written to an HDF5 dataset at path "/data" in a new HDF5 file.
    """

    FILE_SUFFIX = ".h5"  # used in parent class
    FORMAT = "hdf5"

    @classmethod
    def write_array(
        cls, array: Union[List, np.ndarray], output_file_path_no_suffix: Union[str, Path]
    ):
        """Write an array to an HDF5 file."""
        # TODO do not assume that there is only one by this name
        # add suffix to the file name
        if isinstance(output_file_path_no_suffix, str):
            output_file_path_no_suffix = Path(output_file_path_no_suffix)
        output_file_path = output_file_path_no_suffix.parent / (
            output_file_path_no_suffix.name + cls.FILE_SUFFIX
        )
        with h5py.File(output_file_path, "w") as f:
            f.create_dataset("data", data=array)
        return output_file_path
