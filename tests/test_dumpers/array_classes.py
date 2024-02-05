from __future__ import annotations
import numpy as np
from pydantic import BaseModel as BaseModel, ConfigDict,  Field


metamodel_version = "None"
version = "None"

class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra = 'forbid',
        arbitrary_types_allowed=True,
        use_enum_values = True)
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




# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
TemperatureDataset.model_rebuild()
TemperatureMatrix.model_rebuild()
LatitudeSeries.model_rebuild()
LongitudeSeries.model_rebuild()
DaySeries.model_rebuild()

