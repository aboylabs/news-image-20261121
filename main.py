#!/usr/bin/env python3
"""Ship the finished 21 November 2026 front page.

The newspaper image lives in this repository as entry.png. Running this
program drops an exact copy at $MAKEFUN_OUTPUT_DIR/entry.png (falling back
to /output/entry.png) and checks the copy before it exits: the bytes match
the source, the file is at most 1 MiB, and the PNG header declares 1024 by
1024. Pure standard library; the program draws nothing and fetches nothing.
"""

import hashlib
import os
import shutil
import struct
import sys

LIMIT = 1_048_576
EDGE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def abort(reason):
    print(f"error: {reason}", file=sys.stderr)
    return 1


def png_size(data):
    """Pull (width, height) out of a PNG's IHDR chunk; None when broken."""
    if len(data) < 33:
        return None
    if data[:8] != PNG_MAGIC:
        return None
    if data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def inspect(path, label):
    """Read a PNG and confirm it is a 1024x1024 image within the size cap."""
    try:
        with open(path, "rb") as stream:
            data = stream.read()
    except OSError as exc:
        return None, f"cannot read {label} image: {exc}"
    size = len(data)
    if size > LIMIT:
        return None, f"{label} image is {size} bytes, over the 1 MiB limit"
    dims = png_size(data)
    if dims is None:
        return None, f"{label} image is not a well-formed PNG with an IHDR chunk"
    if dims != (EDGE, EDGE):
        return None, f"{label} image is {dims[0]}x{dims[1]}, expected 1024x1024"
    return data, None


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    origin = os.path.join(base, "entry.png")
    dest_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dest = os.path.join(dest_dir, "entry.png")

    if not os.path.isfile(origin):
        return abort(f"missing source image: {origin}")
    source_data, problem = inspect(origin, "source")
    if problem:
        return abort(problem)

    os.makedirs(dest_dir, exist_ok=True)
    shutil.copyfile(origin, dest)

    if hashlib.sha256(source_data).hexdigest() != sha256_of(dest):
        return abort("copy digest mismatch after writing the image")
    target_data, problem = inspect(dest, "output")
    if problem:
        return abort(problem)

    print(f"entry.png written: 1024x1024 {len(target_data)} bytes "
          f"sha256 {sha256_of(dest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
