import unittest

from pathlib import Path
import numpy as np
from linkml_arrays.dumpers import YAMLNumpyDumper
from linkml_runtime import SchemaView

from tests.test_dumpers.array_classes import LatitudeSeries, LongitudeSeries, DaySeries, TemperatureMatrix


class YamlNumpyDumpersTestCase(unittest.TestCase):
    """
    Test dumping of pydantic-style classes from LinkML schemas into YAML + Numpy arrays
    """

    def test_dump_pydantic_arrays(self):
        lat = LatitudeSeries(values=np.array([1, 2, 3]))
        lon = LongitudeSeries(values=np.array([4, 5, 6]))
        day = DaySeries(values=np.array([7, 8, 9]))
        temperature = TemperatureMatrix(
            name="my_temperature",
            x=lat,
            y=lon,
            time=day,
            temperatures=np.ones((3, 3, 3)),
        )

        schemaview = SchemaView(Path(__file__) / "../../input/temperature_matrix.yaml")
        ret = YAMLNumpyDumper().dumps(temperature, schemaview=schemaview)

        expected = """name: my_temperature
temperatures: saved in TemperatureMatrix.temperatures.npy
time:
  values: saved in my_temperature.DaySeries.values.npy
x:
  values: saved in my_temperature.LatitudeSeries.values.npy
y:
  values: saved in my_temperature.LongitudeSeries.values.npy
"""
        assert ret == expected


