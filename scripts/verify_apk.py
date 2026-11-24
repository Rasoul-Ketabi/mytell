#!/usr/bin/env python3
"""Independent APK ZIP/DEX validator. Packaging checks only; no runtime security claims."""
import argparse
import hashlib
import json
import struct
import zipfile
import zlib
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("apk", type=Path)
args = parser.parse_args()

with args.apk.open("rb") as raw, zipfile.ZipFile(raw) as z:
    assert z.testzip() is None, "Damaged ZIP entry"
    info = z.getinfo("resources.arsc")
    assert info.compress_type == zipfile.ZIP_STORED, "resources.arsc is compressed"

    # ZipInfo.extra describes the CENTRAL directory, not the LOCAL header.
    # Android maps uncompressed resources directly from the local ZIP entry.
    raw.seek(info.header_offset)
    local = raw.read(30)
    assert len(local) == 30 and local[:4] == bytes.fromhex("504b0304"), "Invalid local header"
    fields = struct.unpack("<IHHHHHIIIHH", local)
    name_len, local_extra_len = fields[-2:]
    raw_name = raw.read(name_len)
    assert raw_name == b"resources.arsc", "Unexpected filename in local header"
    resources_data_offset = info.header_offset + 30 + name_len + local_extra_len
    assert resources_data_offset % 4 == 0, (
        "resources.arsc data offset not 4-byte aligned: "
        + str(resources_data_offset)
    )

    scanned = 0
    for name in z.namelist():
        content = z.read(name)
        lower = content.lower()
        assert b"itellapp.com" not in lower, "Old ASCII domain in " + name
        assert "itellapp.com".encode("utf-16le") not in lower, "Old UTF-16LE domain in " + name
        scanned += 1
    dex = z.read("classes.dex")
    assert hashlib.sha1(dex[32:]).digest() == dex[12:32], "DEX SHA-1 mismatch"
    assert (zlib.adler32(dex[12:]) & 0xffffffff) == struct.unpack_from("<I", dex, 8)[0], (
        "DEX Adler32 mismatch"
    )

print(json.dumps({
    "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
    "entries_checked": scanned,
    "resources_stored": True,
    "resources_data_offset": resources_data_offset,
    "resources_aligned": True,
    "dex_checksums_valid": True,
    "explicit_legacy_domain_literals_found": False,
    "warning": "Static checks cannot prove runtime safety or iOS pairing.",
}, indent=2))
