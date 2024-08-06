"""Class for dumping a LinkML model to YAML with paths to NumPy files."""

from pathlib import Path
from typing import List, Union

import numpy as np
import xarray as xr

from .yaml_array_file_dumper import YamlArrayFileDumper


class YamlXarrayNetCDFDumper(YamlArrayFileDumper):
    """Dumper class for LinkML models to YAML with paths to .nc file.

    Each array is written to a netcdf dataset at path "/data" in a new .nc file.
    """

    FILE_SUFFIX = ".nc"  # used in parent class
    FORMAT = "netcdf"

    @classmethod
    def write_array(
        cls, array: Union[List, np.ndarray], output_file_path_no_suffix: Union[str, Path]
    ):
        """Write an array to a NumPy file."""
        # TODO do not assume that there is only one by this name
        # add suffix to the file name
        if isinstance(output_file_path_no_suffix, str):
            output_file_path_no_suffix = Path(output_file_path_no_suffix)
        output_file_path = output_file_path_no_suffix.parent / (
            output_file_path_no_suffix.name + cls.FILE_SUFFIX
        )

        data_array = xr.DataArray(data=array)
        data_array.to_netcdf(output_file_path, engine="h5netcdf")
        return output_file_path


class YamlXarrayZarrDumper(YamlArrayFileDumper):
    """Dumper class for LinkML models to YAML with paths to .zarr file.

    Each array is written to a zarr dataset at path "/data" in a new .zarr file.
    """

    FILE_SUFFIX = ".zarr"  # used in parent class
    FORMAT = "zarr"

    @classmethod
    def write_array(
        cls, array: Union[List, np.ndarray], output_file_path_no_suffix: Union[str, Path]
    ):
        """Write an array to a NumPy file."""
        # TODO do not assume that there is only one by this name
        # add suffix to the file name
        if isinstance(output_file_path_no_suffix, str):
            output_file_path_no_suffix = Path(output_file_path_no_suffix)
        output_file_path = output_file_path_no_suffix.parent / (
            output_file_path_no_suffix.name + cls.FILE_SUFFIX
        )

        data_array = xr.DataArray(data=array)
        data_array.to_zarr(output_file_path)
        return output_file_path