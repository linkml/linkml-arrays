from typing import Union

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from anndata import AnnData
from geopandas import GeoDataFrame
from multiscale_spatial_image import MultiscaleSpatialImage
from numpy.random import default_rng
from shapely.geometry import MultiPolygon, Point, Polygon
from spatial_image import SpatialImage
from spatialdata import SpatialData
from spatialdata.models import (
    Image2DModel,
    Image3DModel,
    Labels2DModel,
    Labels3DModel,
    PointsModel,
    ShapesModel,
    TableModel,
)
from xarray import DataArray

# Added from https://github.com/scverse/spatialdata-plot

RNG = default_rng()


@pytest.fixture()
def full_sdata() -> SpatialData:
    return SpatialData(
        images=_get_images(),
        labels=_get_labels(),
        shapes=_get_shapes(),
        points=_get_points(),
        table=_get_table(region="sample1"),
    )


def _get_images() -> dict[str, Union[SpatialImage, MultiscaleSpatialImage]]:
    out = {}
    dims_2d = ("c", "y", "x")
    dims_3d = ("z", "y", "x", "c")
    out["image2d"] = Image2DModel.parse(
        RNG.normal(size=(3, 64, 64)), dims=dims_2d, c_coords=["r", "g", "b"]
    )
    out["image2d_multiscale"] = Image2DModel.parse(
        RNG.normal(size=(3, 64, 64)), scale_factors=[2, 2], dims=dims_2d, c_coords=["r", "g", "b"]
    )
    out["image2d_xarray"] = Image2DModel.parse(
        DataArray(RNG.normal(size=(3, 64, 64)), dims=dims_2d), dims=None
    )
    out["image2d_multiscale_xarray"] = Image2DModel.parse(
        DataArray(RNG.normal(size=(3, 64, 64)), dims=dims_2d),
        scale_factors=[2, 4],
        dims=None,
    )
    out["image3d_numpy"] = Image3DModel.parse(RNG.normal(size=(2, 64, 64, 3)), dims=dims_3d)
    out["image3d_multiscale_numpy"] = Image3DModel.parse(
        RNG.normal(size=(2, 64, 64, 3)), scale_factors=[2], dims=dims_3d
    )
    out["image3d_xarray"] = Image3DModel.parse(
        DataArray(RNG.normal(size=(2, 64, 64, 3)), dims=dims_3d), dims=None
    )
    out["image3d_multiscale_xarray"] = Image3DModel.parse(
        DataArray(RNG.normal(size=(2, 64, 64, 3)), dims=dims_3d),
        scale_factors=[2],
        dims=None,
    )
    return out


def _get_labels() -> dict[str, Union[SpatialImage, MultiscaleSpatialImage]]:
    out = {}
    dims_2d = ("y", "x")
    dims_3d = ("z", "y", "x")

    out["labels2d"] = Labels2DModel.parse(RNG.integers(0, 100, size=(64, 64)), dims=dims_2d)
    out["labels2d_multiscale"] = Labels2DModel.parse(
        RNG.integers(0, 100, size=(64, 64)), scale_factors=[2, 4], dims=dims_2d
    )
    out["labels2d_xarray"] = Labels2DModel.parse(
        DataArray(RNG.integers(0, 100, size=(64, 64)), dims=dims_2d), dims=None
    )
    out["labels2d_multiscale_xarray"] = Labels2DModel.parse(
        DataArray(RNG.integers(0, 100, size=(64, 64)), dims=dims_2d),
        scale_factors=[2, 4],
        dims=None,
    )
    out["labels3d_numpy"] = Labels3DModel.parse(
        RNG.integers(0, 100, size=(10, 64, 64)), dims=dims_3d
    )
    out["labels3d_multiscale_numpy"] = Labels3DModel.parse(
        RNG.integers(0, 100, size=(10, 64, 64)), scale_factors=[2, 4], dims=dims_3d
    )
    out["labels3d_xarray"] = Labels3DModel.parse(
        DataArray(RNG.integers(0, 100, size=(10, 64, 64)), dims=dims_3d), dims=None
    )
    out["labels3d_multiscale_xarray"] = Labels3DModel.parse(
        DataArray(RNG.integers(0, 100, size=(10, 64, 64)), dims=dims_3d),
        scale_factors=[2, 4],
        dims=None,
    )
    return out


def _get_polygons() -> dict[str, GeoDataFrame]:
    out = {}
    poly = GeoDataFrame(
        {
            "geometry": [
                Polygon(((0, 0), (0, 1), (1, 1), (1, 0))),
                Polygon(((0, 0), (0, -1), (-1, -1), (-1, 0))),
                Polygon(((0, 0), (0, 1), (1, 10))),
                Polygon(((0, 0), (0, 1), (1, 1))),
                Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (1, 0))),
            ]
        }
    )

    multipoly = GeoDataFrame(
        {
            "geometry": [
                MultiPolygon(
                    [
                        Polygon(((0, 0), (0, 1), (1, 1), (1, 0))),
                        Polygon(((0, 0), (0, -1), (-1, -1), (-1, 0))),
                    ]
                ),
                MultiPolygon(
                    [
                        Polygon(((0, 0), (0, 1), (1, 10))),
                        Polygon(((0, 0), (0, 1), (1, 1))),
                        Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (1, 0))),
                    ]
                ),
            ]
        }
    )

    out["poly"] = ShapesModel.parse(poly, name="poly")
    out["multipoly"] = ShapesModel.parse(multipoly, name="multipoly")

    return out


def _get_shapes() -> dict[str, AnnData]:
    out = {}
    poly = GeoDataFrame(
        {
            "geometry": [
                Polygon(((0, 0), (0, 1), (1, 1), (1, 0))),
                Polygon(((0, 0), (0, -1), (-1, -1), (-1, 0))),
                Polygon(((0, 0), (0, 1), (1, 10))),
                Polygon(((10, 10), (10, 20), (20, 20))),
                Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (1, 0))),
            ]
        }
    )

    multipoly = GeoDataFrame(
        {
            "geometry": [
                MultiPolygon(
                    [
                        Polygon(((0, 0), (0, 1), (1, 1), (1, 0))),
                        Polygon(((0, 0), (0, -1), (-1, -1), (-1, 0))),
                    ]
                ),
                MultiPolygon(
                    [
                        Polygon(((0, 0), (0, 1), (1, 10))),
                        Polygon(((0, 0), (1, 0), (1, 1))),
                    ]
                ),
            ]
        }
    )

    points = GeoDataFrame(
        {
            "geometry": [
                Point((0, 1)),
                Point((1, 1)),
                Point((3, 4)),
                Point((4, 2)),
                Point((5, 6)),
            ]
        }
    )
    rng = np.random.default_rng(seed=0)
    points["radius"] = np.abs(rng.normal(size=(len(points), 1)))

    out["poly"] = ShapesModel.parse(poly)
    out["poly"].index = [0, 1, 2, 3, 4]
    out["multipoly"] = ShapesModel.parse(multipoly)
    out["circles"] = ShapesModel.parse(points)

    return out


def _get_points() -> dict[str, pa.Table]:
    name = "points"
    out = {}
    for i in range(2):
        name = f"{name}_{i}"
        arr = RNG.normal(size=(300, 2))
        # randomly assign some values from v to the points
        points_assignment0 = RNG.integers(0, 10, size=arr.shape[0]).astype(np.int_)
        if i == 0:
            genes = RNG.choice(["a", "b"], size=arr.shape[0])
        else:
            # we need to test the case in which we have a categorical column with more than 127 categories, see full
            # explanation in write_points() (the parser will convert this column to a categorical since
            # feature_key="genes")
            genes = np.tile(np.array(list(map(str, range(280)))), 2)[:300]
        annotation = pd.DataFrame(
            {
                "genes": genes,
                "instance_id": points_assignment0,
            },
        )
        out[name] = PointsModel.parse(
            arr, annotation=annotation, feature_key="genes", instance_key="instance_id"
        )
    return out


def _get_table(
    region: None | str | list[str] = "sample1",
    region_key: None | str = "region",
    instance_key: None | str = "instance_id",
) -> AnnData:
    adata = AnnData(
        RNG.normal(size=(100, 10)),
        obs=pd.DataFrame(RNG.normal(size=(100, 3)), columns=["a", "b", "c"]),
    )
    if not all(var for var in (region, region_key, instance_key)):
        return TableModel.parse(adata=adata)
    adata.obs[instance_key] = np.arange(adata.n_obs)
    if isinstance(region, str):
        adata.obs[region_key] = region
    elif isinstance(region, list):
        adata.obs[region_key] = RNG.choice(region, size=adata.n_obs)
    return TableModel.parse(
        adata=adata, region=region, region_key=region_key, instance_key=instance_key
    )
