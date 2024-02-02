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

    schema_path = Path(__file__) / "../../input/temperature_dataset.yaml"
    schemaview = SchemaView(schema_path)

Then use a dumper to serialize the ``TemperatureDataset`` data object that we created above:

YAML + NumPy dumper:

.. code:: python

    from linkml_arrays.dumpers import YamlNumpyDumper
    YamlNumpyDumper().dumps(temperature, schemaview=schemaview)

YAML + HDF5 dumper:

.. code:: python

    from linkml_arrays.dumpers import YamlHdf5Dumper
    YamlHdf5Dumper().dumps(temperature, schemaview=schemaview)

HDF5 dumper:

.. code:: python

    from linkml_arrays.dumpers import Hdf5Dumper
    Hdf5Dumper().dumps(temperature, schemaview=schemaview)

Zarr dumper:

.. code:: python

    from linkml_arrays.dumpers import ZarrDumper
    ZarrDumper().dumps(temperature, schemaview=schemaview)
