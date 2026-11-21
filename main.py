#!/usr/bin/env python3
"""Deliver the 21 November 2026 front page.

The repository holds the finished page as entry.png. This program places a
byte-identical copy at $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png
when the variable is unset) and proves the copy before it exits: same SHA-256
as the source, at most 1 MiB, and a PNG header that says 1024 by 1024.
Standard library only; nothing is drawn or downloaded here.
"""

import hashlib
import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
SIDE = 1024


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 1


def png_dimensions(blob):
    """Return (width, height) from a PNG byte string, or None if malformed."""
    if len(blob) < 33 or blob[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if blob[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", blob[16:24])
    return width, height


def digest_of(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target = os.path.join(out_dir, "entry.png")

    if not os.path.isfile(source):
        return fail(f"missing source image: {source}")
    with open(source, "rb") as handle:
        source_blob = handle.read()
    source_dims = png_dimensions(source_blob)
    if source_dims is None:
        return fail("source image is not a well-formed PNG with an IHDR chunk")
    if source_dims != (SIDE, SIDE):
        return fail(f"source image is {source_dims[0]}x{source_dims[1]}, "
                     "expected 1024x1024")
    os.makedirs(out_dir, exist_ok=True)

    shutil.copyfile(source, target)

    want = digest_of(source)
    got = digest_of(target)
    if want != got:
        return fail("copy digest mismatch after writing the image")

    size = os.path.getsize(target)
    if size > MAX_BYTES:
        return fail(f"image is {size} bytes, over the 1 MiB limit")

    with open(target, "rb") as handle:
        blob = handle.read()
    dims = png_dimensions(blob)
    if dims is None:
        return fail("output is not a well-formed PNG with an IHDR chunk")
    if dims != (SIDE, SIDE):
        return fail(f"image is {dims[0]}x{dims[1]}, expected 1024x1024")

    print(f"entry.png written: 1024x1024 {size} bytes sha256 {got}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
