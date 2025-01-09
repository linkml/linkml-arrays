# linkml-arrays

This repository serves as an example repository showcasing the support for loading and dumping
N-dimensional arrays, including labeled arrays in LinkML. The examples are a work in progress,
which are used at the same time to develop the metadata model for arrays in LinkML.

## Dumpers and loaders
The repository currently includes dumpers and loaders examples
for `yaml`, `hdf5`, `numpy` and `zarr`.

## Data

<ins>Temperature dataset</ins>

The schema defining the labeled array according to the linkml array metamodel can 
be found here `tests/input/temperature_schema.yaml`. The schema defines a `DataArray`
similar to an `xarray.DataArray`. The schema includes an array of values `TemperaturesInKMatrix`, 
and labeled dimensions which correspond to the concept of `coordinates` in `xarray`.

# Quick reference for common commands

```bash
poetry run gen-pydantic tests/input/temperature_schema.yaml > tests/array_classes_lol.py
```

# Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
