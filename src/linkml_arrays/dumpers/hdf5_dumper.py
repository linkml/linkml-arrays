"""Class for dumping a LinkML model to an HDF5 file."""

from pathlib import Path
from typing import Union

import h5py
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_arrays.graph_utils.graph import ObjectGraph
from linkml_arrays.graph_utils.serializers import Hdf5GraphSerializer


class Hdf5Dumper(Dumper):
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
        graph = ObjectGraph.from_root(element, schemaview)

        with h5py.File(output_file_path, "w") as f:
            serializer = Hdf5GraphSerializer(
                graph=graph,
                h5file=f,
            )
            serializer.serialize()
