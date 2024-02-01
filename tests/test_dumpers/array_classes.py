from __future__ import annotations

import re
import sys
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel as BaseModel
from pydantic import Field, validator

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


metamodel_version = "None"
version = "None"


class WeakRefShimBaseModel(BaseModel):
    __slots__ = "__weakref__"


class ConfiguredBaseModel(
    WeakRefShimBaseModel,
    validate_assignment=True,
    validate_all=True,
    underscore_attrs_are_private=True,
    extra="forbid",
    arbitrary_types_allowed=True,
    use_enum_values=True,
):
    pass


class TemperatureDataset(ConfiguredBaseModel):

    name: str = Field(...)
    latitude_in_deg: LatitudeSeries = Field(...)
    longitude_in_deg: LongitudeSeries = Field(...)
    time_in_d: DaySeries = Field(...)
    temperatures_in_K: TemperatureMatrix = Field(...)


class TemperatureMatrix(ConfiguredBaseModel):
    """
    A 3D array of temperatures
    """

    values: np.ndarray = Field(None)


class LatitudeSeries(ConfiguredBaseModel):
    """
    A series whose values represent latitude
    """

    values: np.ndarray = Field(None)


class LongitudeSeries(ConfiguredBaseModel):
    """
    A series whose values represent longitude
    """

    values: np.ndarray = Field(None)


class DaySeries(ConfiguredBaseModel):
    """
    A series whose values represent the days since the start of the measurement period
    """

    values: np.ndarray = Field(None)


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
TemperatureDataset.update_forward_refs()
TemperatureMatrix.update_forward_refs()
LatitudeSeries.update_forward_refs()
LongitudeSeries.update_forward_refs()
DaySeries.update_forward_refs()
