"""Test dumping LinkML models in pydantic-style classes to various file formats."""

import os
import unittest
from pathlib import Path

import numpy as np
from linkml_runtime import SchemaView

from linkml_arrays.dumpers import (
    Hdf5Dumper,
    YamlDumper,
    YamlHdf5Dumper,
    YamlNumpyDumper,
    ZarrDirectoryStoreDumper,
)
from tests.test_dumpers.array_classes import (
    DaySeries,
    LatitudeSeries,
    LongitudeSeries,
    TemperatureDataset,
    TemperatureMatrix,
)


class YamlDumpersTestCase(unittest.TestCase):
    """Test dumping of pydantic-style classes from LinkML schemas into YAML files."""

    def test_dump_pydantic_arrays(self):
        """Test dumping pydantic classes with numpy arrays to a YAML file."""
        latitude_in_deg = LatitudeSeries(values=np.array([1, 2]))
        longitude_in_deg = LongitudeSeries(values=np.array([4, 5]))
        time_in_d = DaySeries(values=np.array([7, 8]))
        temperatures_in_K = TemperatureMatrix(
            values=np.arange(8).reshape((2, 2, 2)),
        )
        temperature = TemperatureDataset(
            name="my_temperature",
            latitude_in_deg=latitude_in_deg,
            longitude_in_deg=longitude_in_deg,
            time_in_d=time_in_d,
            temperatures_in_K=temperatures_in_K,
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlDumper().dumps(temperature, schemaview=schemaview)

        expected = """latitude_in_deg:
  values:
  - 1
  - 2
longitude_in_deg:
  values:
  - 4
  - 5
name: my_temperature
temperatures_in_K:
  values:
  - - - 0
      - 1
    - - 2
      - 3
  - - - 4
      - 5
    - - 6
      - 7
time_in_d:
  values:
  - 7
  - 8
"""
        assert ret == expected


class YamlNumpyDumpersTestCase(unittest.TestCase):
    """Test dumping of pydantic-style classes from LinkML schemas into YAML + NumPy files."""

    def test_dump_pydantic_arrays(self):
        """Test dumping pydantic classes with numpy arrays to a YAML + NumPy files."""
        latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
        longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
        time_in_d = DaySeries(values=np.array([7, 8, 9]))
        temperatures_in_K = TemperatureMatrix(
            values=np.ones((3, 3, 3)),
        )
        temperature = TemperatureDataset(
            name="my_temperature",
            latitude_in_deg=latitude_in_deg,
            longitude_in_deg=longitude_in_deg,
            time_in_d=time_in_d,
            temperatures_in_K=temperatures_in_K,
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlNumpyDumper().dumps(temperature, schemaview=schemaview)

        expected = """latitude_in_deg:
  values: file:./my_temperature.LatitudeSeries.values.npy
longitude_in_deg:
  values: file:./my_temperature.LongitudeSeries.values.npy
name: my_temperature
temperatures_in_K:
  values: file:./my_temperature.TemperatureMatrix.values.npy
time_in_d:
  values: file:./my_temperature.DaySeries.values.npy
"""
        assert ret == expected


class YamlHdf5DumpersTestCase(unittest.TestCase):
    """Test dumping of pydantic-style classes from LinkML schemas into YAML + HDF5 datasets."""

    def test_dump_pydantic_arrays(self):
        """Test dumping pydantic classes with numpy arrays to a YAML + HDF5 datasets."""
        latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
        longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
        time_in_d = DaySeries(values=np.array([7, 8, 9]))
        temperatures_in_K = TemperatureMatrix(
            values=np.ones((3, 3, 3)),
        )
        temperature = TemperatureDataset(
            name="my_temperature",
            latitude_in_deg=latitude_in_deg,
            longitude_in_deg=longitude_in_deg,
            time_in_d=time_in_d,
            temperatures_in_K=temperatures_in_K,
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlHdf5Dumper().dumps(temperature, schemaview=schemaview)

        expected = """latitude_in_deg:
  values: file:./my_temperature.LatitudeSeries.values.h5
longitude_in_deg:
  values: file:./my_temperature.LongitudeSeries.values.h5
name: my_temperature
temperatures_in_K:
  values: file:./my_temperature.TemperatureMatrix.values.h5
time_in_d:
  values: file:./my_temperature.DaySeries.values.h5
"""
        assert ret == expected


class Hdf5DumpersTestCase(unittest.TestCase):
    """Test dumping of pydantic-style classes from LinkML schemas into a single HDF5 file."""

    def test_dump_pydantic_arrays(self):
        """Test dumping pydantic classes with numpy arrays to a signle HDF5 file."""
        latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
        longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
        time_in_d = DaySeries(values=np.array([7, 8, 9]))
        temperatures_in_K = TemperatureMatrix(
            values=np.ones((3, 3, 3)),
        )
        temperature = TemperatureDataset(
            name="my_temperature",
            latitude_in_deg=latitude_in_deg,
            longitude_in_deg=longitude_in_deg,
            time_in_d=time_in_d,
            temperatures_in_K=temperatures_in_K,
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        Hdf5Dumper().dumps(temperature, schemaview=schemaview)

        assert os.path.exists("my_temperature.h5")

        # TODO use h5py to assert that the data is correct


class ZarrDirectoryStoreDumpersTestCase(unittest.TestCase):
    """Test dumping of pydantic-style classes from LinkML schemas into a Zarr directory store."""

    def test_dump_pydantic_arrays(self):
        """Test dumping pydantic classes with numpy arrays to a Zarr directory store."""
        latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
        longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
        time_in_d = DaySeries(values=np.array([7, 8, 9]))
        temperatures_in_K = TemperatureMatrix(
            values=np.ones((3, 3, 3)),
        )
        temperature = TemperatureDataset(
            name="my_temperature",
            latitude_in_deg=latitude_in_deg,
            longitude_in_deg=longitude_in_deg,
            time_in_d=time_in_d,
            temperatures_in_K=temperatures_in_K,
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ZarrDirectoryStoreDumper().dumps(temperature, schemaview=schemaview)

        assert os.path.exists("my_temperature.zarr")

        # TODO use Zarr to assert that the data is correct
