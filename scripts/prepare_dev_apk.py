#!/usr/bin/env python3
"""SHA-pinned experimental APK recovery. No source-level rebuild."""
import argparse
import hashlib
import json
import struct
import zipfile
import zlib
from pathlib import Path

EXPECTED_APK_SHA256 = "ea715b2f6e254dbd6083ed1338f10dc0845b725e561ab33b47e91d9df5f05ca7"
EXPECTED_DEX_SHA256 = "cb76cb683d32900fa4c9bf780081a3aa8958bc16a75970e53284480f366a3b61"
REPLACEMENTS = [
    (b"itellapp.com", b"offline.test"),
    ("itellapp.com".encode("utf-16le"), "offline.test".encode("utf-16le")),
]
PATCHES = [
    (0x2df44 + 16 + 34 * 2, "39030500", "29000b00", "development account state"),
    (0x2e63c + 16, "6200a90a", "0e000000", "suppress obsolete account status"),
    (0xaea54 + 16, "6200a90a", "12100f00", "commercial entitlement gate in BridgeService"),
]

def dex_checksums(data):
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I", data, 8, zlib.adler32(data[12:]) & 0xffffffff)

def build(source_path, output_path, report_path):
    actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if actual != EXPECTED_APK_SHA256:
        raise ValueError(f"Wrong source APK SHA256: {actual}")
    report = {"source_sha256": actual, "classification": "UNTESTED_DEV_BINARY_PATCH", "patches": [], "domain_replacements": {}}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_path) as src, zipfile.ZipFile(output_path, "w", allowZip64=False) as dst:
        dex = bytearray(src.read("classes.dex"))
        if hashlib.sha256(dex).hexdigest() != EXPECTED_DEX_SHA256:
            raise ValueError("Wrong original classes.dex SHA256")
        for offset, old_s, new_s, reason in PATCHES:
            old, new = bytes.fromhex(old_s), bytes.fromhex(new_s)
            if dex[offset:offset + len(old)] != old or len(new) != len(old):
                raise ValueError(f"Original DEX patch precondition failed at 0x{offset:x}")
            dex[offset:offset + len(old)] = new
            report["patches"].append({"offset": hex(offset), "reason": reason})
        for item in src.infolist():
            name = item.filename
            if name.startswith("META-INF/") and name.lower().endswith((".rsa", ".dsa", ".ec", ".sf", "manifest.mf")):
                continue
            content = bytes(dex) if name == "classes.dex" else src.read(name)
            hits = 0
            for old, new in REPLACEMENTS:
                if len(old) != len(new):
                    raise ValueError("Not a same-size substitution")
                hits += content.count(old)
                content = content.replace(old, new)
            if hits:
                report["domain_replacements"][name] = hits
            if name == "classes.dex":
                buf = bytearray(content)
                dex_checksums(buf)
                content = bytes(buf)
            for old, _ in REPLACEMENTS:
                if old in content:
                    raise ValueError("Legacy domain still present in " + name)
            dst.writestr(item, content)
    report["unsigned_apk_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    report["known_limitations"] = [
        "Binary changes are experimental and not validated against Android runtime.",
        "Literal domain replacement does not establish network safety.",
        "iOS 1.3 pairing and server-signed link certificate compatibility are unverified.",
        "Commercial checks in native/Shell voice components may still block audio.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Prepared unsigned APK; domain replacements:", sum(report["domain_replacements"].values()))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args()
    build(options.source, options.output, options.report)
