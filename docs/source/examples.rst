..  _examples:

-------------
Example Usage
-------------

Given a LinkML schema such as the following:
https://github.com/linkml/linkml-arrays/blob/main/tests/input/temperature_dataset.yaml

We can generate Pydantic classes for the schema:
https://github.com/linkml/linkml-arrays/blob/main/tests/test_dumpers/array_classes.py

We can then create instances of these classes to represent data:

.. code:: python

    import numpy as np
    from tests.test_dumpers.array_classes import (
        LatitudeSeries, LongitudeSeries, DaySeries,
        TemperatureMatrix, TemperatureDataset
    )

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

^^^^^^^^^^^^^
Serialization
^^^^^^^^^^^^^

We currently have four options for serializing (dumper) these arrays to disk:

1. a YAML file for the non-array data and a NumPy file for each of the arrays
2. a YAML file for the non-array data and an HDF5 file with a single dataset for each of the arrays
3. a single HDF5 file with a hierarchical structure that mirrors the structure of the data object and contains
   non-array data as attributes and array data as datasets
4. a single Zarr (v2) directory store with a hierarchical structure that mirrors the structure of the data object and
   contains non-array data as attributes and array data as arrays

For all dumpers, first get a ``SchemaView`` object for the LinkML schema:

.. code:: python

    from linkml_runtime import SchemaView
    from pathlib import Path

    schema_path = Path("temperature_dataset.yaml")
    schemaview = SchemaView(schema_path)

Then use a dumper to serialize the ``TemperatureDataset`` data object that we created above:

YAML + NumPy dumper:

.. code:: python

    from linkml_arrays.dumpers import YamlNumpyDumper
    YamlNumpyDumper().dumps(temperature, schemaview=schemaview)

Output YAML file with references to the NumPy files for each array:

.. code:: yaml

    latitude_in_deg:
      values: file:./my_temperature.LatitudeSeries.values.npy
    longitude_in_deg:
      values: file:./my_temperature.LongitudeSeries.values.npy
    name: my_temperature
    temperatures_in_K:
      values: file:./my_temperature.TemperatureMatrix.values.npy
    time_in_d:
      values: file:./my_temperature.DaySeries.values.npy

YAML + HDF5 dumper:

.. code:: python

    from linkml_arrays.dumpers import YamlHdf5Dumper
    YamlHdf5Dumper().dumps(temperature, schemaview=schemaview)

Output YAML file with references to the HDF5 files for each array:

.. code:: yaml

    latitude_in_deg:
      values: file:./my_temperature.LatitudeSeries.values.h5
    longitude_in_deg:
      values: file:./my_temperature.LongitudeSeries.values.h5
    name: my_temperature
    temperatures_in_K:
      values: file:./my_temperature.TemperatureMatrix.values.h5
    time_in_d:
      values: file:./my_temperature.DaySeries.values.h5

HDF5 dumper:

.. code:: python

    from linkml_arrays.dumpers import Hdf5Dumper
    Hdf5Dumper().dumps(temperature, schemaview=schemaview)

The ``h5dump`` output of the resulting HDF5 file:

.. code::

    HDF5 "my_temperature.h5" {
    GROUP "/" {
      ATTRIBUTE "name" {
          DATATYPE  H5T_STRING {
            STRSIZE H5T_VARIABLE;
            STRPAD H5T_STR_NULLTERM;
            CSET H5T_CSET_UTF8;
            CTYPE H5T_C_S1;
          }
          DATASPACE  SCALAR
          DATA {
          (0): "my_temperature"
          }
      }
      GROUP "latitude_in_deg" {
          DATASET "values" {
            DATATYPE  H5T_STD_I64LE
            DATASPACE  SIMPLE { ( 3 ) / ( 3 ) }
            DATA {
            (0): 1, 2, 3
            }
          }
      }
      GROUP "longitude_in_deg" {
          DATASET "values" {
            DATATYPE  H5T_STD_I64LE
            DATASPACE  SIMPLE { ( 3 ) / ( 3 ) }
            DATA {
            (0): 4, 5, 6
            }
          }
      }
      GROUP "temperatures_in_K" {
          DATASET "values" {
            DATATYPE  H5T_IEEE_F64LE
            DATASPACE  SIMPLE { ( 3, 3, 3 ) / ( 3, 3, 3 ) }
            DATA {
            (0,0,0): 1, 1, 1,
            (0,1,0): 1, 1, 1,
            (0,2,0): 1, 1, 1,
            (1,0,0): 1, 1, 1,
            (1,1,0): 1, 1, 1,
            (1,2,0): 1, 1, 1,
            (2,0,0): 1, 1, 1,
            (2,1,0): 1, 1, 1,
            (2,2,0): 1, 1, 1
            }
          }
      }
      GROUP "time_in_d" {
          DATASET "values" {
            DATATYPE  H5T_STD_I64LE
            DATASPACE  SIMPLE { ( 3 ) / ( 3 ) }
            DATA {
            (0): 7, 8, 9
            }
          }
      }
    }
    }

Zarr dumper:

.. code:: python

    from linkml_arrays.dumpers import ZarrDumper
    ZarrDumper().dumps(temperature, schemaview=schemaview)

The ``tree`` output of the resulting Zarr directory store:

.. code::

    my_temperature.zarr
    ├── .zattrs
    ├── .zgroup
    ├── latitude_in_deg
    │   ├── .zgroup
    │   └── values
    │       ├── .zarray
    │       └── 0
    ├── longitude_in_deg
    │   ├── .zgroup
    │   └── values
    │       ├── .zarray
    │       └── 0
    ├── temperatures_in_K
    │   ├── .zgroup
    │   └── values
    │       ├── .zarray
    │       └── 0.0.0
    └── time_in_d
        ├── .zgroup
        └── values
            ├── .zarray
            └── 0

^^^^^^^^^^^^^^^
Deserialization
^^^^^^^^^^^^^^^

For deserializing (loading) the data, we can use the corresponding loader for each dumper:

YAML + NumPy loader:

.. code:: python

    from hbreader import hbread
    from linkml_arrays.loaders import YamlNumpyLoader

    read_yaml = hbread("my_temperature_yaml_numpy.yaml")
    read_temperature = YamlNumpyLoader().loads(read_yaml, target_class=TemperatureDataset, schemaview=schemaview)

YAML + HDF5 loader:

.. code:: python

    from hbreader import hbread
    from linkml_arrays.loaders import YamlHdf5Loader

    read_yaml = hbread("my_temperature_yaml_hdf5.yaml")
    read_temperature = YamlHdf5Loader().loads(read_yaml, target_class=TemperatureDataset, schemaview=schemaview)

HDF5 loader:

.. code:: python

    from linkml_arrays.loaders import Hdf5Loader

    read_temperature = Hdf5Loader().loads("my_temperature.h5", target_class=Temperature

Zarr loader:

.. code:: python

    from linkml_arrays.loaders import ZarrLoader

    read_temperature = ZarrLoader().loads("my_temperature.zarr", target_class=Temperature