#!/usr/bin/env python3
"""Repackage a SHA-guarded Build49 DEV APK for Android11 TLS exporter support.

The output replaces exactly two method refs and adds bundled Conscrypt DEX/native libs.
All ADB authentication, SPAKE2, TLS labels and QR/BLE pairing remain unchanged.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

PATCHES = {
    "T.smali": (
        "Ljavax/net/ssl/SSLContext;->getInstance(Ljava/lang/String;)Ljavax/net/ssl/SSLContext;",
        "Lcom/itellapp/android/compat/AdbTlsCompat;->getContext(Ljava/lang/String;)Ljavax/net/ssl/SSLContext;"
    ),
    "Lc.smali": (
        "Landroid/net/ssl/SSLSockets;->exportKeyingMaterial(Ljavax/net/ssl/SSLSocket;Ljava/lang/String;[BI)[B",
        "Lcom/itellapp/android/compat/AdbTlsCompat;->exportKeyingMaterial(Ljavax/net/ssl/SSLSocket;Ljava/lang/String;[BI)[B"
    ),
}

def run(*args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def repair_ble_gatt_when_qr_refresh(smali_root):
    """Repair only a missing GATT server when the existing QR refresh callback runs.

    On healthy/previously paired devices, behaviour is bytecode-equivalent to the
    original branch: if server != null, skip straight to original code. No QR,
    ECDH, BLE MAC, authorization or iOS protocol changes.
    """
    import re
    path = smali_root / "com/itellapp/android/BridgeService.smali"
    data = path.read_text(encoding="utf-8")
    pattern = r"(?ms)^\\.method[^\\n]*\\sa0\\(\\)V\\s*\\n.*?^\\.end method"
    matches = list(re.finditer(pattern, data))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one BridgeService.a0()V, got {len(matches)}")
    method = matches[0].group()
    count = re.search(r"(?m)^[ \\t]+\\.(locals|registers)[ \\t]+(\\d+)[ \\t]*$", method)
    if not count:
        raise RuntimeError("No register declaration in BridgeService.a0()V")
    old_count = int(count.group(2))
    n = old_count if count.group(1) == "locals" else old_count - 1
    if n < 0 or n >= 16:
        raise RuntimeError(f"Unsafe GATT compatibility register index: {n}")
    label = re.search(r"(?m)^[ \\t]*:try_start[^\\n]*$", method)
    if not label:
        raise RuntimeError("No protected try block in BridgeService.a0()V")
    patch = (
        f"\\n    iget-object v{n}, p0, Lcom/itellapp/android/BridgeService;->b:Landroid/bluetooth/BluetoothGattServer;\\n"
        f"    if-nez v{n}, :itell_gatt_existing\\n"
        "    invoke-virtual {p0}, Lcom/itellapp/android/BridgeService;->r0()V\\n"
        "    :itell_gatt_existing\\n"
    )
    if "itell_gatt_existing" in method:
        raise RuntimeError("GATT repair already injected")
    method = method[:count.start(2)] + str(old_count + 1) + method[count.end(2):]
    label = re.search(r"(?m)^[ \\t]*:try_start[^\\n]*$", method)
    method = method[:label.end()] + patch + method[label.end():]
    path.write_text(data[:matches[0].start()] + method + data[matches[0].end():], encoding="utf-8")
    return "BridgeService.a0()V: reopen GATT only if null when QR refresh arrives"

def execute(args):
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="itell-tls30-") as tmp:
        tmp = Path(tmp)
        smali_root = tmp / "smali"
        dex_input = tmp / "classes.dex"
        dex_output = tmp / "classes-fixed.dex"
        with zipfile.ZipFile(args.input) as zin:
            assert zin.testzip() is None
            entries = zin.namelist()
            assert entries.count("classes.dex") == 1
            assert not any(name.startswith("classes2.dex") for name in entries)
            assert not any(name.startswith("lib/") and "conscrypt" in name.lower() for name in entries)
            dex_input.write_bytes(zin.read("classes.dex"))
        run("java", "-jar", args.baksmali, "d", dex_input, "-o", smali_root)
        applied = []
        for relative, (old, new) in PATCHES.items():
            path = smali_root / relative
            if not path.is_file():
                raise RuntimeError("Cannot find target smali: " + str(path))
            data = path.read_text(encoding="utf-8")
            count = data.count(old)
            if count != 1:
                raise RuntimeError(f"Expected one method reference in {relative}; found {count}")
            data = data.replace(old, new)
            assert old not in data and data.count(new) == 1
            path.write_text(data, encoding="utf-8")
            applied.append(relative)
        gatt_repair = repair_ble_gatt_when_qr_refresh(smali_root)
        run("java", "-jar", args.smali, "a", smali_root, "-o", dex_output)
        dex_new = dex_output.read_bytes()
        assert dex_new[:4] == b"dex\n"
        with zipfile.ZipFile(args.conscrypt_aar) as aar:
            native = {
                "lib/" + name.removeprefix("jni/"): aar.read(name)
                for name in aar.namelist()
                if name.startswith("jni/")
                and name.endswith("/libconscrypt_jni.so")
                and name.split("/")[1] in ("arm64-v8a", "armeabi-v7a", "x86_64", "x86")
            }
            required = {"lib/arm64-v8a/libconscrypt_jni.so", "lib/armeabi-v7a/libconscrypt_jni.so"}
            if not required <= set(native):
                raise RuntimeError("Conscrypt missing required arm64-v8a or armeabi-v7a library")
        dex_entries = []
        for source_dex in sorted(args.compiled_dex.glob("classes*.dex")):
            name = f"classes{len(dex_entries)+2}.dex"
            dex_entries.append((name, source_dex.read_bytes()))
        if not dex_entries:
            raise RuntimeError("Missing compiled Conscrypt classes dex")
        with zipfile.ZipFile(args.input) as zin, zipfile.ZipFile(args.output, "w", allowZip64=False) as zout:
            for item in zin.infolist():
                data = dex_new if item.filename == "classes.dex" else zin.read(item.filename)
                zout.writestr(item, data)
            for name, data in dex_entries:
                zout.writestr(name, data, compress_type=zipfile.ZIP_STORED)
            for name, data in native.items():
                zout.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(args.output) as z:
            assert z.testzip() is None
            assert z.read("classes.dex") == dex_new
            assert all(z.read(name) == data for name, data in dex_entries)
            assert all(z.read(name) == data for name, data in native.items())
        report = {
            "patch": "API30 authenticated ADB TLS exporter using isolated Conscrypt",
            "exact_bytecode_targets": applied,
            "qr_gatt_repair": gatt_repair,
            "pairing_security": "ADB pairing parameters, TrustManager, TLS 1.3, SPAKE2, QR and BLE unchanged",
            "original_main_dex_sha256": sha(dex_input.read_bytes()),
            "rewritten_main_dex_sha256": sha(dex_new),
            "extra_dex_files": [name for name, _ in dex_entries],
            "native_abis": sorted(native),
            "unsigned_apk_sha256": sha(args.output.read_bytes()),
            "real_device_pairing": "NOT TESTED"
        }
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for field in ("input", "output", "report", "smali", "baksmali", "conscrypt-aar", "compiled-dex"):
        p.add_argument("--" + field, required=True, type=Path)
    execute(p.parse_args())
