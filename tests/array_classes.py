from __future__ import annotations 
from datetime import (
    datetime,
    date
)
from decimal import Decimal 
from enum import Enum 
import re
import sys
from pydantic.version import VERSION  as PYDANTIC_VERSION 
from typing import (
    Any,
    ClassVar,
    List,
    Literal,
    Dict,
    Optional,
    Union,
    Generic,
    Iterable,
    TypeVar,
    get_args
)
if sys.version_info.minor > 8:
    from typing import Annotated 
else:
    from typing_extensions import Annotated 

from pydantic import GetCoreSchemaHandler 
from pydantic_core import (
    CoreSchema,
    core_schema
)
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


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass




class LinkMLMeta(RootModel):
    root: Dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value



_T = TypeVar("_T")

_RecursiveListType = Iterable[Union[_T, Iterable["_RecursiveListType"]]]

class AnyShapeArrayType(Generic[_T]):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        # double-nested parameterized types here
        # source_type: List[Union[T,List[...]]]
        item_type = Any if get_args(get_args(source_type)[0])[0] is _T else get_args(get_args(source_type)[0])[0]

        item_schema = handler.generate_schema(item_type)
        if item_schema.get("type", "any") != "any":
            item_schema["strict"] = True

        if item_type is Any:
            # Before python 3.11, `Any` type was a special object without a __name__
            item_name = "Any"
        else:
            item_name = item_type.__name__

        array_ref = f"any-shape-array-{item_name}"

        schema = core_schema.definitions_schema(
            core_schema.list_schema(core_schema.definition_reference_schema(array_ref)),
            [
                core_schema.union_schema(
                    [
                        core_schema.list_schema(core_schema.definition_reference_schema(array_ref)),
                        item_schema,
                    ],
                    ref=array_ref,
                )
            ],
        )

        return schema


AnyShapeArray = Annotated[_RecursiveListType, AnyShapeArrayType]
linkml_meta = LinkMLMeta({'default_prefix': 'https://example.org/arrays/',
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
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays', 'tree_root': True})

    name: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']} })
    temperature_dataset: TemperatureDataset = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'temperature_dataset', 'domain_of': ['Container']} })
    latitude_series: LatitudeInDegSeries = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'latitude_series', 'domain_of': ['Container']} })
    longitude_series: LongitudeInDegSeries = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'longitude_series', 'domain_of': ['Container']} })


class TemperatureDataset(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays',
         'implements': ['linkml:DataArray'],
         'tree_root': True})

    name: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']} })
    latitude_in_deg: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'latitude_in_deg', 'domain_of': ['TemperatureDataset']} })
    longitude_in_deg: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'longitude_in_deg', 'domain_of': ['TemperatureDataset']} })
    date: DateSeries = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'date', 'domain_of': ['TemperatureDataset']} })
    day_in_d: Optional[DaysInDSinceSeries] = Field(None, json_schema_extra = { "linkml_meta": {'alias': 'day_in_d', 'domain_of': ['TemperatureDataset']} })
    temperatures_in_K: AnyShapeArray[TemperaturesInKMatrix] = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'temperatures_in_K',
         'array': {'annotations': {'labeled_by': {'tag': 'labeled_by',
                                                  'value': ' - alias: lat label_slot: '
                                                           'latitude_in_deg '
                                                           'labeled_dimensions: [0, 1] '
                                                           '- alias: lon label_slot: '
                                                           'longitude_in_deg '
                                                           'labeled_dimensions: [0, 1] '
                                                           '- alias: date label_slot: '
                                                           'date labeled_dimensions: '
                                                           '[2] - alias: day '
                                                           'label_slot: day_in_d '
                                                           'labeled_dimensions: '
                                                           '[2] '}}},
         'domain_of': ['TemperatureDataset']} })


class LatitudeInDegSeries(ConfiguredBaseModel):
    """
    A 2D array whose values represent latitude
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays'})

    name: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']} })
    values: List[List[float]] = Field(default_factory=list, json_schema_extra = { "linkml_meta": {'alias': 'values',
         'array': {'exact_number_dimensions': 2},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'deg'}} })


class LongitudeInDegSeries(ConfiguredBaseModel):
    """
    A 2D array whose values represent longitude
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays'})

    name: str = Field(..., json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Container',
                       'TemperatureDataset',
                       'LatitudeInDegSeries',
                       'LongitudeInDegSeries']} })
    values: List[List[float]] = Field(default_factory=list, json_schema_extra = { "linkml_meta": {'alias': 'values',
         'array': {'exact_number_dimensions': 2},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'deg'}} })


class DateSeries(ConfiguredBaseModel):
    """
    A 1D series of dates
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays'})

    values: List[str] = Field(default_factory=list, json_schema_extra = { "linkml_meta": {'alias': 'values',
         'array': {'exact_number_dimensions': 1},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix']} })


class DaysInDSinceSeries(ConfiguredBaseModel):
    """
    A 1D series whose values represent the number of days since a reference date
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays'})

    values: List[int] = Field(default_factory=list, json_schema_extra = { "linkml_meta": {'alias': 'values',
         'array': {'exact_number_dimensions': 1},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'd'}} })
    reference_date: str = Field(..., description="""The reference date for the `day_in_d` values""", json_schema_extra = { "linkml_meta": {'alias': 'reference_date', 'domain_of': ['DaysInDSinceSeries']} })


class TemperaturesInKMatrix(ConfiguredBaseModel):
    """
    A 3D array of temperatures
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://example.org/arrays'})

    conversion_factor: Optional[float] = Field(None, description="""A conversion factor to apply to the temperature values""", json_schema_extra = { "linkml_meta": {'alias': 'conversion_factor',
         'domain_of': ['TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'K'}} })
    values: List[List[List[float]]] = Field(default_factory=list, json_schema_extra = { "linkml_meta": {'alias': 'values',
         'array': {'dimensions': [{'alias': 'x'}, {'alias': 'y'}, {'alias': 'date'}],
                   'exact_number_dimensions': 3},
         'domain_of': ['LatitudeInDegSeries',
                       'LongitudeInDegSeries',
                       'DateSeries',
                       'DaysInDSinceSeries',
                       'TemperaturesInKMatrix'],
         'unit': {'ucum_code': 'K'}} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Container.model_rebuild()
TemperatureDataset.model_rebuild()
LatitudeInDegSeries.model_rebuild()
LongitudeInDegSeries.model_rebuild()
DateSeries.model_rebuild()
DaysInDSinceSeries.model_rebuild()
TemperaturesInKMatrix.model_rebuild()

