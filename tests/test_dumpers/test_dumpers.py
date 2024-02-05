import os
import unittest
from pathlib import Path

import numpy as np
from linkml_runtime import SchemaView

from linkml_arrays.dumpers import (
    Hdf5Dumper,
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


class YamlNumpyDumpersTestCase(unittest.TestCase):
    """
    Test dumping of pydantic-style classes from LinkML schemas into YAML + Numpy arrays
    """

    def test_dump_pydantic_arrays(self):
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
    """
    Test dumping of pydantic-style classes from LinkML schemas into YAML + HDF5 datasets
    """

    def test_dump_pydantic_arrays(self):
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
    """
    Test dumping of pydantic-style classes from LinkML schemas into a single HDF5 file
    """

    def test_dump_pydantic_arrays(self):
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


class ZarrDirectoryStoreDumpersTestCase(unittest.TestCase):
    """
    Test dumping of pydantic-style classes from LinkML schemas into a single Zarr directory store
    """

    def test_dump_pydantic_arrays(self):
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
