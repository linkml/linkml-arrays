from __future__ import annotations 
from datetime import (
    datetime,
    date
)
from decimal import Decimal 
from enum import Enum 
import re
import sys
from typing import (
    Any,
    ClassVar,
    List,
    Literal,
    Dict,
    Optional,
    Union
)
from pydantic.version import VERSION  as PYDANTIC_VERSION 
if int(PYDANTIC_VERSION[0])>=2:
    from pydantic import (
        BaseModel,
        ConfigDict,
        Field,
        RootModel,
        field_validator
    )
else:
    from pydantic import (
        BaseModel,
        Field,
        validator
    )

from pydantic import conlist 
metamodel_version = "None"
version = "None"


class WeakRefShimBaseModel(BaseModel):
    __slots__ = '__weakref__'

class ConfiguredBaseModel(WeakRefShimBaseModel,
                validate_assignment = True,
                validate_all = True,
                underscore_attrs_are_private = True,
                extra = "forbid",
                arbitrary_types_allowed = True,
                use_enum_values = True):
    pass




class LinkMLMeta(BaseModel):
    __root__: Dict[str, Any] = {}

    def __getattr__(self, key:str):
        return getattr(self.__root__, key)

    def __getitem__(self, key:str):
        return self.__root__[key]

    def __setitem__(self, key:str, value):
        self.__root__[key] = value

    class Config:
        allow_mutation = False

linkml_meta = LinkMLMeta(__root__={'default_prefix': 'https://example.org/arrays/',
     'description': 'Example LinkML schema to demonstrate a 3D DataArray of '
                    'temperature values with labeled axes\n'
                    'using classes containing arrays for the axes and data instead '
                    'of using array slots/attributes.\n'
                    'Creating separate types for the array slots enables reuse and '
                    'extension.',
     'id': 'https://example.org/arrays',
     'name': 'arrays-temperature-example-2'} )


class Container(ConfiguredBaseModel):
    """
    A container for a temperature dataset
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays', 'tree_root': True})

    name: str = Field(..., linkml_meta = {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']}
)
    temperature_dataset: TemperatureDataset = Field(..., linkml_meta = {'alias': 'temperature_dataset', 'domain_of': ['Container']}
)
    latitude_series: LatitudeInDegSeries = Field(..., linkml_meta = {'alias': 'latitude_series', 'domain_of': ['Container']}
)
    longitude_series: LongitudeInDegSeries = Field(..., linkml_meta = {'alias': 'longitude_series', 'domain_of': ['Container']}
)


class TemperatureDataset(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays',
         'implements': ['linkml:DataArray'],
         'tree_root': True})

    name: str = Field(..., linkml_meta = {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']}
)
    latitude_in_deg: str = Field(..., linkml_meta = {'alias': 'latitude_in_deg', 'domain_of': ['TemperatureDataset']}
)
    longitude_in_deg: str = Field(..., linkml_meta = {'alias': 'longitude_in_deg', 'domain_of': ['TemperatureDataset']}
)
    date: DateSeries = Field(..., linkml_meta = {'alias': 'date', 'domain_of': ['TemperatureDataset']}
)
    day_in_d: Optional[DaysInDSinceSeries] = Field(None, linkml_meta = {'alias': 'day_in_d', 'domain_of': ['TemperatureDataset']}
)
    temperatures_in_K: TemperaturesInKMatrix = Field(..., linkml_meta = {'alias': 'temperatures_in_K', 'domain_of': ['TemperatureDataset']}
)


class LatitudeInDegSeries(ConfiguredBaseModel):
    """
    A 2D array whose values represent latitude
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays'})

    name: str = Field(..., linkml_meta = {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']}
)
    values: List[List[float]] = Field(default_factory=list, linkml_meta = {'alias': 'values',
         'array': {'exact_number_dimensions': 2},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'deg'}}
)


class LongitudeInDegSeries(ConfiguredBaseModel):
    """
    A 2D array whose values represent longitude
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays'})

    name: str = Field(..., linkml_meta = {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']}
)
    values: List[List[float]] = Field(default_factory=list, linkml_meta = {'alias': 'values',
         'array': {'exact_number_dimensions': 2},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'deg'}}
)


class DateSeries(ConfiguredBaseModel):
    """
    A 1D series of dates
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays'})

    values: List[str] = Field(default_factory=list, linkml_meta = {'alias': 'values',
         'array': {'exact_number_dimensions': 1},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix']}
)


class DaysInDSinceSeries(ConfiguredBaseModel):
    """
    A 1D series whose values represent the number of days since a reference date
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays'})

    values: List[int] = Field(default_factory=list, linkml_meta = {'alias': 'values',
         'array': {'exact_number_dimensions': 1},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'd'}}
)
    reference_date: str = Field(..., description="""The reference date for the `day_in_d` values""", linkml_meta = {'alias': 'reference_date', 'domain_of': ['DaysInDSinceSeries']}
)


class TemperaturesInKMatrix(ConfiguredBaseModel):
    """
    A 3D array of temperatures
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(__root__={'from_schema': 'https://example.org/arrays'})

    conversion_factor: Optional[float] = Field(None, description="""A conversion factor to apply to the temperature values""", linkml_meta = {'alias': 'conversion_factor',
         'domain_of': ['TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'K'}}
)
    values: List[List[List[float]]] = Field(default_factory=list, linkml_meta = {'alias': 'values',
         'array': {'dimensions': [{'alias': 'x'}, {'alias': 'y'}, {'alias': 'date'}],
                   'exact_number_dimensions': 3},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'K'}}
)


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
Container.update_forward_refs()
TemperatureDataset.update_forward_refs()
LatitudeInDegSeries.update_forward_refs()
LongitudeInDegSeries.update_forward_refs()
DateSeries.update_forward_refs()
DaysInDSinceSeries.update_forward_refs()
TemperaturesInKMatrix.update_forward_refs()

