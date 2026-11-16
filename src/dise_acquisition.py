"""Read selected members of a remote ZIP without mirroring the archive."""

from __future__ import annotations

import io
import re

import requests


class HTTPRangeFile(io.RawIOBase):
    """Seekable, bounded range reader; reject ignored ranges and source changes."""

    def __init__(self, url, block_size=1024**2):
        self.url = url
        self.session = requests.Session()
        self.block_size = block_size
        self.position = 0
        self.cache_start = 0
        self.cache = b""
        self.requests = 0
        self.transferred = 0
        self.etag = None
        self.size = None
        self._fetch(0, 0)

    def _fetch(self, start, end):
        headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
        if self.etag:
            headers["If-Match"] = self.etag
        with self.session.get(self.url, headers=headers, stream=True, timeout=(20, 90)) as r:
            if r.status_code != 206:
                raise OSError(f"Range request requires 206, received {r.status_code}")
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", r.headers.get("Content-Range", ""))
            if not match:
                raise OSError("Missing or malformed Content-Range")
            actual_start, actual_end, total = map(int, match.groups())
            if (actual_start, actual_end) != (start, end):
                raise OSError("Server returned a different byte range")
            etag = r.headers.get("ETag")
            if self.size is not None and (self.size != total or self.etag != etag):
                raise OSError("Remote archive identity changed during acquisition")
            data = r.raw.read(end - start + 2, decode_content=False)
            if len(data) != end - start + 1:
                raise OSError("Truncated or oversized range response")
        self.size, self.etag = total, etag
        self.requests += 1
        self.transferred += len(data)
        return data

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        target = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if whence not in (0, 1, 2) or target < 0:
            raise ValueError("Invalid seek")
        self.position = target
        return target

    def read(self, size=-1):
        if size < 0:
            size = self.size - self.position
            if size > 8 * 1024**2:
                raise OSError("Unbounded remote reads larger than 8 MiB are disabled")
        size = min(size, max(0, self.size - self.position))
        if not size:
            return b""
        end = self.position + size
        if not (self.cache_start <= self.position and end <= self.cache_start + len(self.cache)):
            self.cache_start = self.position
            last = min(self.size, max(end, self.position + self.block_size)) - 1
            self.cache = self._fetch(self.position, last)
        result = self.cache[self.position - self.cache_start:end - self.cache_start]
        self.position = end
        return result

    def close(self):
        self.session.close()
        super().close()
