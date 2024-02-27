from pathlib import Path

from spatialdata import SpatialData


class TestWriteRead:
    def test_write_read(
        self,
        tmp_path: str,
        full_sdata: SpatialData,
    ) -> None:
        tmpdir = Path(tmp_path) / "tmp.zarr"
        full_sdata.write(tmpdir)
        SpatialData.read(tmpdir)
