from __future__ import annotations
from datetime import datetime, date
from enum import Enum
import numpy as np
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel as BaseModel, Field, validator
import re
import sys
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


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


class TimestampSeries(ConfiguredBaseModel):
    
    None
    
    

class IrregularlySampledTimestampSeries(TimestampSeries):
    
    name: str = Field(...)
    values: Union[np.ndarray, NDArrayProxy] = Field(...)
    
    

class RegularlySampledTimestampSeries(TimestampSeries):
    
    name: str = Field(...)
    sampling_rate: float = Field(...)
    starting_time: float = Field(...)
    length: Optional[int] = Field(None)
    values: Optional[Union[np.ndarray, NDArrayProxy]] = Field(None)
    
    

class Electrode(ConfiguredBaseModel):
    
    name: str = Field(...)
    impedance: Optional[float] = Field(None)
    
    

class ElectrodeSeries(ConfiguredBaseModel):
    
    values: Union[np.ndarray, NDArrayProxy] = Field(...)
    
    

class ElectricalDataMatrix(ConfiguredBaseModel):
    """
    A 2D array of electrode voltage measurements over time. See ElectricalDataArray for its usage with axes labels.
    """
    values: Union[np.ndarray, NDArrayProxy] = Field(...)
    
    

class ElectricalDataArray(ConfiguredBaseModel):
    
    time: TimestampSeries = Field(...)
    electrode: ElectrodeSeries = Field(...)
    values: ElectricalDataMatrix = Field(...)
    
    

class IrregularlySampledElectricalDataArray(ElectricalDataArray):
    
    time: IrregularlySampledTimestampSeries = Field(...)
    electrode: ElectrodeSeries = Field(...)
    values: ElectricalDataMatrix = Field(...)
    
    

class RegularlySampledElectricalDataArray(ElectricalDataArray):
    
    time: Optional[str] = Field(None)
    electrode: ElectrodeSeries = Field(...)
    values: ElectricalDataMatrix = Field(...)
    
    

class File(ConfiguredBaseModel):
    
    electrical_data_arrays: Optional[List[ElectricalDataArray]] = Field(default_factory=list)
    electrodes: Optional[List[Electrode]] = Field(default_factory=list)
    
    


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
TimestampSeries.update_forward_refs()
IrregularlySampledTimestampSeries.update_forward_refs()
RegularlySampledTimestampSeries.update_forward_refs()
Electrode.update_forward_refs()
ElectrodeSeries.update_forward_refs()
ElectricalDataMatrix.update_forward_refs()
ElectricalDataArray.update_forward_refs()
IrregularlySampledElectricalDataArray.update_forward_refs()
RegularlySampledElectricalDataArray.update_forward_refs()
File.update_forward_refs()

