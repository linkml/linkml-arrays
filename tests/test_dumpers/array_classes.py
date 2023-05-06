from __future__ import annotations
from datetime import datetime, date
from enum import Enum
import numpy as np
from typing import List, Dict, Optional, Any, Union, Literal
from pydantic import BaseModel as BaseModel, Field
from linkml_runtime.linkml_model import Decimal

metamodel_version = "None"
version = "None"

class WeakRefShimBaseModel(BaseModel):
   __slots__ = '__weakref__'

class ConfiguredBaseModel(WeakRefShimBaseModel,
                validate_assignment = True,
                validate_all = True,
                underscore_attrs_are_private = True,
                extra = 'forbid',
                arbitrary_types_allowed = True,
                use_enum_values = True):
    pass


class TemperatureMatrix(ConfiguredBaseModel):

    x: LatitudeSeries = Field(None)
    y: LongitudeSeries = Field(None)
    time: DaySeries = Field(None)
    temperatures: np.ndarray = Field(None)



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
TemperatureMatrix.update_forward_refs()
LatitudeSeries.update_forward_refs()
LongitudeSeries.update_forward_refs()
DaySeries.update_forward_refs()