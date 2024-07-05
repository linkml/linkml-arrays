"""Test loading data from various file formats into LinkML pydantic models with arrays as lists-of-lists."""

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
from tests.array_classes_lol import (
    Container,
    DateSeries,
    DaysInDSinceSeries,
    LatitudeInDegSeries,
    LongitudeInDegSeries,
    TemperatureDataset,
    TemperaturesInKMatrix,
)


def check_container(container: Container):
    assert isinstance(container, Container)
    assert container.name == "my_container"

    assert isinstance(container.latitude_series, LatitudeInDegSeries)
    assert container.latitude_series.name == "my_latitude"
    assert container.latitude_series.values == [[1, 2], [3, 4]]

    assert isinstance(container.longitude_series, LongitudeInDegSeries)
    assert container.longitude_series.name == "my_longitude"
    assert container.longitude_series.values == [[5, 6], [7, 8]]

    assert isinstance(container.temperature_dataset, TemperatureDataset)
    assert container.temperature_dataset.name == "my_temperature"
    assert container.temperature_dataset.latitude_in_deg == "my_latitude"
    # currently no way to get the actual LatitudeInDegSeries object from the TemperatureDataset object
    # because the TemperatureDataset Pydantic object expects a string for the latitude_in_deg field
    # to be isomorphic with the json schema / yaml representation

    assert container.temperature_dataset.longitude_in_deg == "my_longitude"

    assert isinstance(container.temperature_dataset.date, DateSeries)
    assert container.temperature_dataset.date.values == ["2020-01-01", "2020-01-02"]

    assert isinstance(container.temperature_dataset.day_in_d, DaysInDSinceSeries)
    assert container.temperature_dataset.day_in_d.values == [0, 1]
    assert container.temperature_dataset.day_in_d.reference_date == "2020-01-01"

    assert isinstance(container.temperature_dataset.temperatures_in_K, TemperaturesInKMatrix)
    assert container.temperature_dataset.temperatures_in_K.values == [
        [[0, 1], [2, 3]],
        [[4, 5], [6, 7]],
    ]


def test_yaml_loader():
    """Test YamlLoader loading pydantic classes from YAML arrays."""
    data_yaml = hbread("container_yaml.yaml", base_path=str(Path(__file__) / "../../input"))
    schemaview = SchemaView(Path(__file__) / "../../input/temperature_schema.yaml")
    container = YamlLoader().loads(data_yaml, target_class=Container, schemaview=schemaview)
    check_container(container)


def test_yaml_numpy_loader():
    """Test loading of pydantic-style classes from YAML + Numpy arrays."""
    read_yaml = hbread("container_yaml_numpy.yaml", base_path=str(Path(__file__) / "../../input"))
    schemaview = SchemaView(Path(__file__) / "../../input/temperature_schema.yaml")
    container = YamlNumpyLoader().loads(read_yaml, target_class=Container, schemaview=schemaview)
    check_container(container)


def test_yaml_hdf5_loader():
    """Test loading of pydantic-style classes from YAML + Numpy arrays."""
    read_yaml = hbread("container_yaml_hdf5.yaml", base_path=str(Path(__file__) / "../../input"))
    schemaview = SchemaView(Path(__file__) / "../../input/temperature_schema.yaml")
    container = YamlHdf5Loader().loads(read_yaml, target_class=Container, schemaview=schemaview)
    check_container(container)


def test_hdf5_loader():
    """Test loading of pydantic-style classes from HDF5 datasets."""
    file_path = str(Path(__file__).parent.parent / "input" / "my_container.h5")
    schemaview = SchemaView(Path(__file__) / "../../input/temperature_schema.yaml")
    container = Hdf5Loader().loads(file_path, target_class=Container, schemaview=schemaview)
    check_container(container)


def test_zarr_directory_store_loader():
    """Test loading of pydantic-style classes from Zarr arrays."""
    file_path = str(Path(__file__).parent.parent / "input" / "my_container.zarr")
    schemaview = SchemaView(Path(__file__) / "../../input/temperature_schema.yaml")
    container = ZarrDirectoryStoreLoader().loads(
        file_path, target_class=Container, schemaview=schemaview
    )
    check_container(container)


# class Hdf5LoadersTestCase(unittest.TestCase):
#     """Test loading of pydantic-style classes from an HDF5 file."""

#     def test_load_pydantic_arrays(self):
#         """Test loading of pydantic-style classes from an HDF5 file."""
#         file_path = str(Path(__file__).parent.parent / "input" / "my_temperature.h5")
#         schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
#         ret = Hdf5Loader().loads(file_path, target_class=TemperatureDataset, schemaview=schemaview)

#         assert isinstance(ret, TemperatureDataset)
#         assert ret.name == "my_temperature"

#         assert isinstance(ret.latitude_in_deg, LatitudeSeries)
#         np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

#         assert isinstance(ret.longitude_in_deg, LongitudeSeries)
#         np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

#         assert isinstance(ret.time_in_d, DaySeries)
#         np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

#         assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
#         np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))


# class ZarrDirectoryStoreLoadersTestCase(unittest.TestCase):
#     """Test loading of pydantic-style classes from a Zarr directory store."""

#     def test_load_pydantic_arrays(self):
#         """Test loading of pydantic-style classes from a Zarr directory store."""
#         file_path = str(Path(__file__).parent.parent / "input" / "my_temperature.zarr")
#         schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
#         ret = ZarrDirectoryStoreLoader().loads(
#             file_path, target_class=TemperatureDataset, schemaview=schemaview
#         )

#         assert isinstance(ret, TemperatureDataset)
#         assert ret.name == "my_temperature"

#         assert isinstance(ret.latitude_in_deg, LatitudeSeries)
#         np.testing.assert_array_equal(ret.latitude_in_deg.values, np.array([1, 2, 3]))

#         assert isinstance(ret.longitude_in_deg, LongitudeSeries)
#         np.testing.assert_array_equal(ret.longitude_in_deg.values, np.array([4, 5, 6]))

#         assert isinstance(ret.time_in_d, DaySeries)
#         np.testing.assert_array_equal(ret.time_in_d.values, np.array([7, 8, 9]))

#         assert isinstance(ret.temperatures_in_K, TemperatureMatrix)
#         np.testing.assert_array_equal(ret.temperatures_in_K.values, np.ones((3, 3, 3)))
