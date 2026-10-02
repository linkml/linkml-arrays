"""Class for dumping a LinkML model to a Zarr directory store."""

from pathlib import Path
from typing import Union

import zarr
from linkml_runtime import SchemaView
from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel
from zarr.storage import LocalStore

from linkml_arrays.graph_utils.graph import ObjectGraph
from linkml_arrays.graph_utils.serializers import ZarrGraphSerializer


class ZarrDirectoryStoreDumper(Dumper):
    """Dumper class for LinkML models to Zarr directory stores."""

    # TODO is this the right method to overwrite? it does not dump a string
    def dumps(
        self,
        element: Union[YAMLRoot, BaseModel],
        schemaview: SchemaView,
        output_file_path: Union[str, Path],
        **kwargs,
    ):
        """Dump the element to a Zarr directory store."""
        graph = ObjectGraph.from_root(element, schemaview)

        store = LocalStore(output_file_path)
        root = zarr.group(store=store, overwrite=True)

        serializer = ZarrGraphSerializer(
            graph=graph,
            root=root,
        )
        serializer.serialize()
