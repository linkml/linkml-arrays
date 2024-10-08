"""Test dumping LinkML pydantic models with arrays as lists-of-lists to various file formats."""

import os
from pathlib import Path

import h5py
import numpy as np
import zarr
from linkml_runtime import SchemaView
from ruamel.yaml import YAML

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


def _create_container() -> Container:
    latitude_in_deg = LatitudeInDegSeries(name="my_latitude", values=[[1, 2], [3, 4]])
    longitude_in_deg = LongitudeInDegSeries(name="my_longitude", values=[[5, 6], [7, 8]])
    date = DateSeries(values=["2020-01-01", "2020-01-02"])
    days_in_d_since = DaysInDSinceSeries(values=[0, 1], reference_date="2020-01-01")
    temperatures_in_K = TemperaturesInKMatrix(
        conversion_factor=1000.0,
        values=[[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
    )
    # NOTE: currently no way to pass in the actual LatitudeInDegSeries object
    temperature_dataset = TemperatureDataset(
        name="my_temperature",
        latitude_in_deg="my_latitude",
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
    container = _create_container()

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
    container = _create_container()

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
    container = _create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    ret = YamlHdf5Dumper().dumps(container, schemaview=schemaview, output_dir="./out")

    # read and compare with the expected YAML file ignoring order of keys
    expected_yaml_file = INPUT_DIR / "container_yaml_hdf5.yaml"
    yaml = YAML(typ="safe")
    with open(expected_yaml_file) as f:
        expected = yaml.load(f)  # load yaml into dictionary
        actual = yaml.load(ret)
        assert actual == expected


def test_hdf5_dumper(tmp_path):
    """Test Hdf5Dumper dumping to an HDF5 file."""
    container = _create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    output_file_path = tmp_path / "my_container.h5"
    Hdf5Dumper().dumps(container, schemaview=schemaview, output_file_path=output_file_path)

    assert os.path.exists(output_file_path)
    with h5py.File(output_file_path, "r") as f:
        assert f.attrs["name"] == "my_container"
        assert set(f["latitude_series"].keys()) == set(["values"])
        np.testing.assert_array_equal(f["latitude_series/values"][:], [[1, 2], [3, 4]])
        assert set(f["longitude_series"].keys()) == set(["values"])
        np.testing.assert_array_equal(f["longitude_series/values"][:], [[5, 6], [7, 8]])
        assert set(f["temperature_dataset"]) == set(["date", "day_in_d", "temperatures_in_K"])
        assert set(f["temperature_dataset/date"].keys()) == set(["values"])
        np.testing.assert_array_equal(
            f["temperature_dataset/date/values"].asstr()[:], np.array(["2020-01-01", "2020-01-02"])
        )
        assert set(f["temperature_dataset/day_in_d"].keys()) == set(["values"])
        assert f["temperature_dataset/day_in_d"].attrs["reference_date"] == "2020-01-01"
        np.testing.assert_array_equal(f["temperature_dataset/day_in_d/values"][:], [0, 1])
        assert set(f["temperature_dataset/temperatures_in_K"].keys()) == set(["values"])
        np.testing.assert_array_equal(
            f["temperature_dataset/temperatures_in_K/values"][:],
            [[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
        )


def test_zarr_directory_store_dumper(tmp_path):
    """Test ZarrDumper dumping to an HDF5 file."""
    container = _create_container()

    schemaview = SchemaView(INPUT_DIR / "temperature_schema.yaml")
    output_file_path = tmp_path / "my_container.zarr"
    ZarrDirectoryStoreDumper().dumps(
        container, schemaview=schemaview, output_file_path=output_file_path
    )

    assert os.path.exists(output_file_path)

    root = zarr.group(store=output_file_path)
    # NOTE this is pretty much the same code as test_hdf5_dumper
    assert root.attrs["name"] == "my_container"
    assert set(root["latitude_series"].keys()) == set(["values"])
    np.testing.assert_array_equal(root["latitude_series/values"][:], [[1, 2], [3, 4]])
    assert set(root["longitude_series"].keys()) == set(["values"])
    np.testing.assert_array_equal(root["longitude_series/values"][:], [[5, 6], [7, 8]])
    assert set(root["temperature_dataset"]) == set(["date", "day_in_d", "temperatures_in_K"])
    assert set(root["temperature_dataset/date"].keys()) == set(["values"])
    np.testing.assert_array_equal(
        root["temperature_dataset/date/values"][:], np.array(["2020-01-01", "2020-01-02"])
    )
    assert set(root["temperature_dataset/day_in_d"].keys()) == set(["values"])
    assert root["temperature_dataset/day_in_d"].attrs["reference_date"] == "2020-01-01"
    np.testing.assert_array_equal(root["temperature_dataset/day_in_d/values"][:], [0, 1])
    assert set(root["temperature_dataset/temperatures_in_K"].keys()) == set(["values"])
    np.testing.assert_array_equal(
        root["temperature_dataset/temperatures_in_K/values"][:],
        [[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
    )
