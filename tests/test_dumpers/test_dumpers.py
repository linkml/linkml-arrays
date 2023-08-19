import unittest

from pathlib import Path
import numpy as np
from linkml_arrays.dumpers import YAMLNumpyDumper
from linkml_runtime import SchemaView

from tests.test_dumpers.array_classes import (
    LatitudeSeries, LongitudeSeries, DaySeries,
    TemperatureMatrix, TemperatureDataset
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
        ret = YAMLNumpyDumper().dumps(temperature, schemaview=schemaview)

        expected = """latitude_in_deg:
  values: file://my_temperature.LatitudeSeries.values.npy
longitude_in_deg:
  values: file://my_temperature.LongitudeSeries.values.npy
name: my_temperature
temperatures_in_K:
  values: file://my_temperature.TemperatureMatrix.values.npy
time_in_d:
  values: file://my_temperature.DaySeries.values.npy
"""
        assert ret == expected


