"""Test dumping LinkML pydantic models with arrays as lists-of-lists to various file formats."""

import os
import unittest
from ruamel.yaml import YAML
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
from tests.array_classes_lol import (
    Container,
    DateSeries,
    DaysInDSinceSeries,
    LatitudeInDegSeries,
    LongitudeInDegSeries,
    TemperatureDataset,
    TemperaturesInKMatrix,
)

INPUT_DIR = Path(__file__).parent.parent / "input"


def create_container() -> Container:
    latitude_in_deg = LatitudeInDegSeries(name="my_latitude", values=[[1, 2], [3, 4]])
    longitude_in_deg = LongitudeInDegSeries(name="my_longitude", values=[[5, 6], [7, 8]])
    date = DateSeries(values=["2020-01-01", "2020-01-02"])
    days_in_d_since = DaysInDSinceSeries(values=[0, 1], reference_date="2020-01-01")
    temperatures_in_K = TemperaturesInKMatrix(
        conversion_factor=1000.0,
        values=[[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
    )
    temperature_dataset = TemperatureDataset(
        name="my_temperature",
        latitude_in_deg="my_latitude",  # currently no way to pass in the actual LatitudeInDegSeries object
        longitude_in_deg="my_longitude",
        date=date,
        day_in_d=days_in_d_since,
        temperatures_in_K=temperatures_in_K,
    )
    container = Container(
        name="my_container",
        latitude_series=latitude_in_deg,
        longitude_series=longitude_in_deg,
        temperature_dataset=temperature_dataset,
    )

    return container


def test_yaml_dumper():
    """Test YamlDumper dumping to a YAML file."""
    container = create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    ret = YamlDumper().dumps(container, schemaview=schemaview)

    # read and compare with the expected YAML file ignoring order of keys
    expected_yaml_file = INPUT_DIR / "container_yaml.yaml"
    yaml = YAML(typ="safe")
    with open(expected_yaml_file) as f:
        expected = yaml.load(f)  # load yaml into dictionary
        actual = yaml.load(ret)
        assert actual == expected


def test_yaml_numpy_dumper():
    """Test YamlNumpyDumper dumping to a YAML file and NumPy .npy files in a directory."""
    container = create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    ret = YamlNumpyDumper().dumps(container, schemaview=schemaview, output_dir="./out")

    # read and compare with the expected YAML file ignoring order of keys
    expected_yaml_file = INPUT_DIR / "container_yaml_numpy.yaml"
    yaml = YAML(typ="safe")
    with open(expected_yaml_file) as f:
        expected = yaml.load(f)  # load yaml into dictionary
        actual = yaml.load(ret)
        assert actual == expected


def test_yaml_hdf5_dumper():
    """Test YamlNumpyDumper dumping to a YAML file and HDF5 datasets in a directory."""
    container = create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    ret = YamlHdf5Dumper().dumps(container, schemaview=schemaview, output_dir="./out")

    # read and compare with the expected YAML file ignoring order of keys
    expected_yaml_file = INPUT_DIR / "container_yaml_hdf5.yaml"
    yaml = YAML(typ="safe")
    with open(expected_yaml_file) as f:
        expected = yaml.load(f)  # load yaml into dictionary
        actual = yaml.load(ret)
        assert actual == expected


# class Hdf5DumpersTestCase(unittest.TestCase):
#     """Test dumping of pydantic-style classes from LinkML schemas into a single HDF5 file."""

#     def test_dump_pydantic_arrays(self):
#         """Test dumping pydantic classes with numpy arrays to a signle HDF5 file."""
#         latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
#         longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
#         time_in_d = DaySeries(values=np.array([7, 8, 9]))
#         temperatures_in_K = TemperatureMatrix(
#             values=np.ones((3, 3, 3)),
#         )
#         temperature = TemperatureDataset(
#             name="my_temperature",
#             latitude_in_deg=latitude_in_deg,
#             longitude_in_deg=longitude_in_deg,
#             time_in_d=time_in_d,
#             temperatures_in_K=temperatures_in_K,
#         )

#         schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
#         Hdf5Dumper().dumps(temperature, schemaview=schemaview)

#         assert os.path.exists("my_temperature.h5")

#         # TODO use h5py to assert that the data is correct


# class ZarrDirectoryStoreDumpersTestCase(unittest.TestCase):
#     """Test dumping of pydantic-style classes from LinkML schemas into a Zarr directory store."""

#     def test_dump_pydantic_arrays(self):
#         """Test dumping pydantic classes with numpy arrays to a Zarr directory store."""
#         latitude_in_deg = LatitudeSeries(values=np.array([1, 2, 3]))
#         longitude_in_deg = LongitudeSeries(values=np.array([4, 5, 6]))
#         time_in_d = DaySeries(values=np.array([7, 8, 9]))
#         temperatures_in_K = TemperatureMatrix(
#             values=np.ones((3, 3, 3)),
#         )
#         temperature = TemperatureDataset(
#             name="my_temperature",
#             latitude_in_deg=latitude_in_deg,
#             longitude_in_deg=longitude_in_deg,
#             time_in_d=time_in_d,
#             temperatures_in_K=temperatures_in_K,
#         )

#         schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
#         ZarrDirectoryStoreDumper().dumps(temperature, schemaview=schemaview)

#         assert os.path.exists("my_temperature.zarr")

#         # TODO use Zarr to assert that the data is correct
