"""Test writing and reading of SpatialData using fixture."""

from pathlib import Path

from spatialdata import SpatialData


class TestWriteRead:
    """Test writing and reading using pytest fixture."""

    def test_write_read(
        self,
        tmp_path: str,
        full_sdata: SpatialData,
    ) -> None:
        """Test writing and reading a SpatialData object with all elements present."""
        tmpdir = Path(tmp_path) / "tmp.zarr"
        full_sdata.write(tmpdir)
        SpatialData.read(tmpdir)
