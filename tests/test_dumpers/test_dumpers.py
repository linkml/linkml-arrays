import unittest
from collections import namedtuple

import numpy as np
from linkml_arrays.dumpers import YAMLNumpyDumper

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
            x=lat,
            y=lon,
            time=day,
            temperatures=np.ones((3, 3, 3)),
        )

        print(YAMLNumpyDumper().dumps(temperature))


