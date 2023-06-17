import unittest

from hbreader import hbread
from pathlib import Path
import numpy as np
from linkml_runtime import SchemaView
from linkml_arrays.loaders import YAMLNumpyLoader

from tests.test_dumpers.array_classes import LatitudeSeries, LongitudeSeries, DaySeries, TemperatureMatrix


class YamlNumpyLoadersTestCase(unittest.TestCase):
    """
    Test loading of pydantic-style classes from YAML + Numpy arrays into LinkML schemas
    """

    def test_load_pydantic_arrays(self):
        read_yaml = hbread("temperature_matrix_dumped.yaml", base_path=str(Path(__file__) / "../../input"))
        schemaview = SchemaView(Path(__file__) / "../../input/temperature_matrix.yaml")
        ret = YAMLNumpyLoader().loads(read_yaml, target_class=TemperatureMatrix, schemaview=schemaview)

        assert isinstance(ret, TemperatureMatrix)
        assert ret.name == "my_temperature"
        np.testing.assert_array_equal(ret.temperatures, np.ones((3, 3, 3)))

        assert isinstance(ret.x, LatitudeSeries)
        np.testing.assert_array_equal(ret.x.values, np.array([1, 2, 3]))

        assert isinstance(ret.y, LongitudeSeries)
        np.testing.assert_array_equal(ret.y.values, np.array([4, 5, 6]))

        assert isinstance(ret.time, DaySeries)
        np.testing.assert_array_equal(ret.time.values, np.array([7, 8, 9]))

