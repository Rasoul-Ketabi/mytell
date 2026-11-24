#!/usr/bin/env python3
"""Verify APK packaging. This is NOT a runtime security or iOS compatibility test."""
import argparse
import hashlib
import json
import struct
import zipfile
import zlib

p = argparse.ArgumentParser()
p.add_argument("apk")
args = p.parse_args()
with zipfile.ZipFile(args.apk) as z:
    assert z.testzip() is None, "Damaged ZIP"
    resources = z.getinfo("resources.arsc")
    assert resources.compress_type == zipfile.ZIP_STORED, "resources.arsc is compressed"
    offset = resources.header_offset + 30 + len(resources.filename.encode("utf-8")) + len(resources.extra)
    assert offset % 4 == 0, f"resources.arsc unaligned at offset {offset}"
    count = 0
    for name in z.namelist():
        data = z.read(name)
        assert b"itellapp.com" not in data.lower(), "Original domain in " + name
        assert "itellapp.com".encode("utf-16le") not in data.lower(), "UTF16 old domain in " + name
        count += 1
    dex = z.read("classes.dex")
    assert hashlib.sha1(dex[32:]).digest() == dex[12:32], "DEX SHA1 mismatch"
    assert zlib.adler32(dex[12:]) & 0xffffffff == struct.unpack_from("<I", dex, 8)[0], "DEX adler32 mismatch"
    print(json.dumps({
        "entries_checked": count,
        "resources_stored": True,
        "resources_data_offset": offset,
        "resources_aligned": True,
        "dex_checksums_valid": True,
        "explicit_legacy_domain_literals_found": False,
        "apk_sha256": hashlib.sha256(open(args.apk, "rb").read()).hexdigest()
    }, indent=2))
