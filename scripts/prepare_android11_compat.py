#!/usr/bin/env python3
"""Android 11 experimental compatibility overlay for an unsigned iTell 1.6 Build 49 DEV APK.

Modify only the typed minSdkVersion attribute (API 31 -> 30) in binary AndroidManifest.xml.
Do not alter targetSdk, DEX, BLE security, pairing, encryption, or call transport.
This overlay alone DOES NOT establish API 30 runtime compatibility.
"""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]

def len8(b, o):
    v = b[o]; o += 1
    if v & 128: v = ((v & 127) << 8) | b[o]; o += 1
    return v, o

def len16(b, o):
    v = u16(b, o); o += 2
    if v & 0x8000: v = ((v & 0x7fff) << 16) | u16(b, o); o += 2
    return v, o

def strings(b, start, end):
    assert u16(b, start) == 1 and u16(b, start+2) >= 28
    count, flags, data_start = u32(b, start+8), u32(b, start+16), u32(b, start+20)
    assert count < 16384
    values = []
    for i in range(count):
        pos = start + data_start + u32(b, start+28+i*4)
        assert start <= pos < end
        if flags & 0x100:
            _, pos = len8(b, pos)
            size, pos = len8(b, pos)
            value = b[pos:pos+size].decode('utf-8')
        else:
            size, pos = len16(b, pos)
            value = b[pos:pos+size*2].decode('utf-16le')
        values.append(value)
    return values

def patch_manifest(original):
    b = bytearray(original)
    assert u16(b, 0) == 3 and u16(b, 2) == 8 and u32(b, 4) == len(b)
    pos, pool, found, edit_pos, before_sdk, target_sdk = 8, None, 0, None, None, None
    while pos < len(b):
        typ, header_size, size = struct.unpack_from('<HHI', b, pos)
        assert size >= header_size >= 8 and pos+size <= len(b)
        if typ == 1:
            assert pool is None
            pool = strings(b, pos, pos+size)
        if typ == 0x102:
            assert pool is not None
            name_id = u32(b, pos+20)
            assert name_id < len(pool)
            if pool[name_id] == 'uses-sdk':
                found += 1
                start, step, count = u16(b, pos+24), u16(b, pos+26), u16(b, pos+28)
                assert step >= 20 and count > 0
                attributes = {}
                for i in range(count):
                    p = pos + 16 + start + i*step
                    assert p+20 <= pos+size
                    key_id = u32(b, p+4)
                    assert key_id < len(pool)
                    key = pool[key_id]
                    if key in ['minSdkVersion', 'targetSdkVersion']:
                        assert u16(b, p+12) == 8 and b[p+15] == 0x10
                        assert key not in attributes
                        attributes[key] = (p+16, u32(b, p+16))
                assert 'minSdkVersion' in attributes and 'targetSdkVersion' in attributes
                edit_pos, before_sdk = attributes['minSdkVersion']
                _, target_sdk = attributes['targetSdkVersion']
                assert before_sdk == 31 and target_sdk == 36, 'Unexpected SDK requirements'
                struct.pack_into('<I', b, edit_pos, 30)
        pos += size
    assert pos == len(b) and found == 1 and edit_pos is not None
    check = bytearray(b)
    struct.pack_into('<I', check, edit_pos, 31)
    assert check == original, 'Unexpected manifest modification'
    return bytes(b), {
        'input_min_sdk': before_sdk,
        'output_min_sdk': 30,
        'target_sdk': target_sdk,
        'manifest_edit_offset': hex(edit_pos),
        'manifest_bytes_changed': sum(a != c for a, c in zip(original, b)),
        'runtime_compatibility': 'NOT VERIFIED until Android 11 smoke test'
    }

def main(src, dst, report):
    dst.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, 'w', allowZip64=False) as zout:
        assert zin.testzip() is None
        details = None
        for item in zin.infolist():
            if item.filename.startswith('META-INF/') and item.filename.lower().endswith(('.rsa', '.dsa', '.ec', '.sf', 'manifest.mf')):
                raise ValueError('Input should be UNSIGNED; old signatures forbidden')
            data = zin.read(item.filename)
            if item.filename == 'AndroidManifest.xml':
                data, details = patch_manifest(data)
            zout.writestr(item, data)
        assert details is not None
    with zipfile.ZipFile(dst) as z:
        assert z.testzip() is None
        details['output_manifest_sha256'] = hashlib.sha256(z.read('AndroidManifest.xml')).hexdigest()
    details['input_unsigned_sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
    details['output_unsigned_sha256'] = hashlib.sha256(dst.read_bytes()).hexdigest()
    report.write_text(json.dumps(details, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(details, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    main(args.input, args.output, args.report)
