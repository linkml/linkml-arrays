import unittest

from hbreader import hbread
from pathlib import Path
import numpy as np
from linkml_runtime import SchemaView
from linkml_arrays.loaders import YAMLNumpyLoader

from tests.test_dumpers.array_classes import (
    LatitudeSeries, LongitudeSeries, DaySeries,
    TemperatureMatrix, TemperatureDataset
)


class YamlNumpyLoadersTestCase(unittest.TestCase):
    """
    Test loading of pydantic-style classes from YAML + Numpy arrays into LinkML schemas
    """

    def test_load_pydantic_arrays(self):
        read_yaml = hbread("temperature_dataset_dumped.yaml", base_path=str(Path(__file__) / "../../input"))
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_dataset.yaml")
        ret = YAMLNumpyLoader().loads(read_yaml, target_class=TemperatureDataset, schemaview=schemaview)

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

