#!/usr/bin/env python3
"""Repackage a SHA-guarded Build49 DEV APK for Android11 TLS exporter support.

The output replaces exactly two method refs and adds bundled Conscrypt DEX/native libs.
All ADB authentication, SPAKE2, TLS labels and QR/BLE pairing remain unchanged.
"""
import argparse
import hashlib
import json
import re
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


def probe_method(path, signature, snippet, add_local=False):
    data = path.read_text(encoding="utf-8")
    pattern = r"(?ms)^\\.method[^\\n]*\\s" + re.escape(signature) + r"\\s*\\n.*?^\\.end method"
    matches = list(re.finditer(pattern, data))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one method {signature} in {path}, got {len(matches)}")
    method = matches[0].group(0)
    head = re.search(r"(?m)^\\s+\\.(locals|registers)\\s+(\\d+)\\s*$", method)
    if not head:
        raise RuntimeError(f"Missing register count for {signature}")
    old = int(head.group(2))
    if add_local:
        n = old if head.group(1) == "locals" else old - 2
        if n < 0:
            raise RuntimeError("Bad register count")
        snippet = snippet.replace("__LOCAL__", "v" + str(n))
        new_count = old + 1
        method = method[:head.start(2)] + str(new_count) + method[head.end(2):]
        head = re.search(r"(?m)^\\s+\\.(locals|registers)\\s+\\d+\\s*$", method)
    if method.count(snippet) != 0:
        raise RuntimeError("Probe injected twice")
    method = method[:head.end()] + "\\n" + snippet + method[head.end():]
    new_data = data[:matches[0].start()] + method + data[matches[0].end():]
    path.write_text(new_data, encoding="utf-8")
    return signature

def inject_ble_qr_probe(root):
    bridge = root / "com/itellapp/android/BridgeService.smali"
    callback = root / "D1.smali"
    for path in (bridge, callback):
        if not path.is_file():
            raise RuntimeError("Missing BLE probe target: " + str(path))
    calls = []
    calls.append(probe_method(
        bridge, "a0()V",
        "    invoke-static {p0}, Lcom/itellapp/android/compat/BleWizardProbe;->onRefresh(Lcom/itellapp/android/BridgeService;)V"
    ))
    calls.append(probe_method(
        callback, "onStartSuccess(Landroid/bluetooth/le/AdvertiseSettings;)V",
        "    iget-object __LOCAL__, p0, LD1;->a:Lcom/itellapp/android/BridgeService;\\n"
        "    invoke-static {__LOCAL__}, Lcom/itellapp/android/compat/BleWizardProbe;->onAdvertisingSuccess(Landroid/content/Context;)V",
        add_local=True
    ))
    calls.append(probe_method(
        callback, "onStartFailure(I)V",
        "    iget-object __LOCAL__, p0, LD1;->a:Lcom/itellapp/android/BridgeService;\\n"
        "    invoke-static {__LOCAL__, p1}, Lcom/itellapp/android/compat/BleWizardProbe;->onAdvertisingFailure(Landroid/content/Context;I)V",
        add_local=True
    ))
    return calls

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
        probe_targets = inject_ble_qr_probe(smali_root)
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
            "ble_qr_probe_targets": probe_targets,
            "exact_bytecode_targets": applied,
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
