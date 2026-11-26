"""Remote ZIP selection must reject full-body responses and range corruption."""

import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_acquisition import HTTPRangeFile


class Response:
    def __init__(self, content, start, end, status=206):
        self.status_code = status
        self.headers = {"Content-Range": f"bytes {start}-{end}/{len(content)}", "ETag": "fixed"}

        class Raw(io.BytesIO):
            def read(self, size=-1, decode_content=False):
                return super().read(size)

        self.raw = Raw(content[start : end + 1])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_zip_member_can_be_selected_without_download_of_other_members(monkeypatch):
    import requests

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("unneeded.bin", b"x" * 100_000)
        z.writestr("selected.csv", b"id,value\na,3\n")
    content = buf.getvalue()

    def get(self, url, headers, **kwargs):
        start, end = map(int, headers["Range"].removeprefix("bytes=").split("-"))
        return Response(content, start, end)

    monkeypatch.setattr(requests.Session, "get", get)
    with HTTPRangeFile("https://example.invalid/data.zip", block_size=256) as remote:
        with zipfile.ZipFile(remote) as z:
            assert z.read("selected.csv") == b"id,value\na,3\n"
        assert remote.transferred < len(content)


def test_range_ignored_cannot_download_the_full_archive(monkeypatch):
    import requests

    monkeypatch.setattr(requests.Session, "get", lambda *a, **kw: Response(b"abc", 0, 0, 200))
    with pytest.raises(OSError, match="requires 206"):
        HTTPRangeFile("https://example.invalid/data.zip")
