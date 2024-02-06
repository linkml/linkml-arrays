"""Test loading data from various file formats into LinkML models."""

import unittest
from pathlib import Path

import numpy as np
from hbreader import hbread
from linkml_runtime import SchemaView

from linkml_arrays.loaders import (
    Hdf5Loader,
    YamlHdf5Loader,
    YamlLoader,
    YamlNumpyLoader,
    ZarrDirectoryStoreLoader,
)
from tests.test_dumpers.array_classes import (
    DaySeries,
    LatitudeSeries,
    LongitudeSeries,
    TemperatureDataset,
    TemperatureMatrix,
)


class YamlLoadersTestCase(unittest.TestCase):
    """Test loading of pydantic-style classes from YAML arrays."""

    def test_load_pydantic_arrays(self):
        """Test loading of pydantic-style classes from YAML arrays."""
        read_yaml = hbread(
            "temperature_dataset_yaml.yaml", base_path=str(Path(__file__) / "../../input")
        )
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlLoader().loads(
            read_yaml, target_class=TemperatureDataset, schemaview=schemaview
        )

        assert isinstance(ret, TemperatureDataset)
        assert ret.name == "my_temperature"

        assert isinstance(ret.latitude_in_deg, LatitudeSeries)
        np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2]))

        assert isinstance(ret.longitude_in_deg, LongitudeSeries)
        np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5]))

        assert isinstance(ret.time_in_d, DaySeries)
        np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8]))

        assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
        np.testing.assert_array_equal(ret.temperatures_in_K.values, np.arange(8).reshape((2, 2, 2)))


class YamlNumpyLoadersTestCase(unittest.TestCase):
    """Test loading of pydantic-style classes from YAML + Numpy arrays."""

    def test_load_pydantic_arrays(self):
        """Test loading of pydantic-style classes from YAML + Numpy arrays."""
        read_yaml = hbread(
            "temperature_dataset_npy_dumped.yaml", base_path=str(Path(__file__) / "../../input")
        )
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlNumpyLoader().loads(
            read_yaml, target_class=TemperatureDataset, schemaview=schemaview
        )

        assert isinstance(ret, TemperatureDataset)
        assert ret.name == "my_temperature"

        assert isinstance(ret.latitude_in_deg, LatitudeSeries)
        np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

        assert isinstance(ret.longitude_in_deg, LongitudeSeries)
        np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

        assert isinstance(ret.time_in_d, DaySeries)
        np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

        assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
        np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))


class YamlHdf5LoadersTestCase(unittest.TestCase):
    """Test loading of pydantic-style classes from YAML + HDF5 datasets."""

    def test_load_pydantic_arrays(self):
        """Test loading of pydantic-style classes from YAML + HDF5 datasets."""
        read_yaml = hbread(
            "temperature_dataset_hdf5_dumped.yaml", base_path=str(Path(__file__) / "../../input")
        )
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YamlHdf5Loader().loads(
            read_yaml, target_class=TemperatureDataset, schemaview=schemaview
        )

        assert isinstance(ret, TemperatureDataset)
        assert ret.name == "my_temperature"

        assert isinstance(ret.latitude_in_deg, LatitudeSeries)
        np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

        assert isinstance(ret.longitude_in_deg, LongitudeSeries)
        np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

        assert isinstance(ret.time_in_d, DaySeries)
        np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

        assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
        np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))


class Hdf5LoadersTestCase(unittest.TestCase):
    """Test loading of pydantic-style classes from an HDF5 file."""

    def test_load_pydantic_arrays(self):
        """Test loading of pydantic-style classes from an HDF5 file."""
        file_path = str(Path(__file__).parent.parent / "input" / "my_temperature.h5")
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = Hdf5Loader().loads(file_path, target_class=TemperatureDataset, schemaview=schemaview)

        assert isinstance(ret, TemperatureDataset)
        assert ret.name == "my_temperature"

        assert isinstance(ret.latitude_in_deg, LatitudeSeries)
        np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

        assert isinstance(ret.longitude_in_deg, LongitudeSeries)
        np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

        assert isinstance(ret.time_in_d, DaySeries)
        np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

        assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
        np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))


class ZarrDirectoryStoreLoadersTestCase(unittest.TestCase):
    """Test loading of pydantic-style classes from a Zarr directory store."""

    def test_load_pydantic_arrays(self):
        """Test loading of pydantic-style classes from a Zarr directory store."""
        file_path = str(Path(__file__).parent.parent / "input" / "my_temperature.zarr")
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = ZarrDirectoryStoreLoader().loads(
            file_path, target_class=TemperatureDataset, schemaview=schemaview
        )

        assert isinstance(ret, TemperatureDataset)
        assert ret.name == "my_temperature"

        assert isinstance(ret.latitude_in_deg, LatitudeSeries)
        np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

        assert isinstance(ret.longitude_in_deg, LongitudeSeries)
        np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

        assert isinstance(ret.time_in_d, DaySeries)
        np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

        assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
        np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))
