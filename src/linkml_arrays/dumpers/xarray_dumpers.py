"""Class for dumping a LinkML model to netcdf like using xarray and DataTree."""

from pathlib import Path

import numpy as np
from xarray.core.datatree import DataTree

"""Class for dumping a LinkML model to an netcdf like file."""

from pathlib import Path
from typing import Union

import xarray as xr
import pandas as pd
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel
from linkml_runtime import SchemaView


def _create_node(model, schemaview):
    """Create datatree from temperature dataset"""
    node_dict = {}
    for k, v in vars(model).items():
        if isinstance(v, str):
            # parts of the dataset with key and value both being string, e.g. name, latitude_in_deg
            try:
                node_dict["attrs"][k] = v
            except KeyError:
                node_dict["attrs"] = {k: v}
        elif isinstance(v, BaseModel):
            if len(var_dict := vars(v)) == 1:
                # If values are length 1 we are dealing with coords like date
                v = pd.to_datetime(v.values)
                try:
                    node_dict["coords"][k] = v
                except KeyError:
                    node_dict["coords"] = {k: {"data": v, "dims": k}}
            else:
                for key, value in var_dict.items():
                    if key == "values":
                        if not isinstance(value[0], list):
                            try:
                                node_dict["coords"][k] = {"data": value, "dims": list(node_dict["coords"])[0]}
                            except KeyError:
                                node_dict["coords"] = {k: {"data": value, "dims": list(node_dict["coords"])[0]}}
                        else:
                            # Parse the temperature matrix
                            element_type = type(v).__name__
                            dimensions_expressions = schemaview.induced_slot(key, element_type).array.dimensions
                            dims = [dim.alias for dim in dimensions_expressions]
                            array = np.array(value)
                            node_dict["dims"] = {dim: array.shape[i] for i, dim in enumerate(dims)}
                            node_dict["data_vars"] = {k: {"data": array, "dims": list(node_dict["dims"].keys())}}
                    else:
                        if isinstance(value, str):
                            # can't use timestamp here as it does not serialize, potentially add with 'data' dims as coord
                            node_dict["coords"][k].update({"attrs": {key: value}})
                        else:
                            # conversion factor
                            node_dict["attrs"][key] = value
    return xr.Dataset.from_dict(node_dict)



def _iterate_element(
    element: Union[YAMLRoot, BaseModel], schemaview: SchemaView, datatree = None
):
    """Recursively iterate through the elements of a LinkML model and save them.

    Write toplevel Pydantic BaseModel objects as datasets, slots with the "array" element
    as datasets, and other slots as attributes.
    """
    # get the type of the element
    element_type = type(element).__name__

    for k, v in vars(element).items():
        if isinstance(v, BaseModel):
            # create a subgroup and recurse
            if "values" in v.__dir__():
                dims = ["y","x"]
                data_dict = vars(v)
                data_dict["data"] = np.array(data_dict.pop("values"))
                data_dict["dims"] = [dims[i] for i in range(data_dict["data"].shape[0])]
                data_dict["attrs"] = {"name": v.name}
                dataarray = xr.DataArray.from_dict(d=data_dict)
                datatree[k] = dataarray
            else:
                dataset = _create_node(v, schemaview)
                datatree[k] = DataTree(data=dataset)
        elif isinstance(v, str):
            datatree.attrs["name"] = v
    return datatree


class XarrayNetCDFDumper(Dumper):
    """Dumper class for LinkML models to HDF5 files."""

    # TODO is this the right method to overwrite? it does not dump a string
    def dumps(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        output_file_path: Union[str, Path],
        **kwargs,
    ):
        """Dump the element to an HDF5 file."""
        datatree = DataTree()
        datatree = _iterate_element(element, schemaview, datatree)
        datatree.to_netcdf(output_file_path, engine='h5netcdf')


class XarrayZarrDumper(Dumper):
    """Dumper class for LinkML models to HDF5 files."""

    # TODO is this the right method to overwrite? it does not dump a string
    def dumps(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        output_file_path: Union[str, Path],
        **kwargs,
    ):
        """Dump the element to an HDF5 file."""
        datatree = DataTree()
        datatree = _iterate_element(element, schemaview, datatree)
        datatree.to_zarr(output_file_path)
