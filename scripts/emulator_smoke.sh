#!/usr/bin/env bash
set -euo pipefail
APK="${1:-dist/itell-dev.apk}"
PKG="com.itellapp.android"
mkdir -p smoke-logs
adb devices -l | tee smoke-logs/devices.txt
adb shell getprop ro.product.cpu.abilist | tee smoke-logs/abis.txt
if ! adb install -r "$APK" > smoke-logs/install.txt 2>&1; then
  cat smoke-logs/install.txt
  adb logcat -d -t 300 > smoke-logs/logcat-install.txt 2>&1 || true
  echo "INSTALL FAILED. Check ABI vs APK's arm64-v8a / armeabi-v7a libraries." >&2
  exit 1
fi
cat smoke-logs/install.txt
adb shell pm path "$PKG" | tee smoke-logs/package.txt
grep -q "package:" smoke-logs/package.txt
adb logcat -c || true
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 | tee smoke-logs/launch.txt
sleep 7
adb logcat -d -t 1200 > smoke-logs/logcat-launch.txt 2>&1 || true
if grep -Ei "FATAL EXCEPTION|Process: com\.itellapp\.android" smoke-logs/logcat-launch.txt > smoke-logs/crash-matches.txt; then
  echo "Crash signature found in launch logs." >&2
  cat smoke-logs/crash-matches.txt
  exit 1
fi
echo "INSTALL AND LAUNCH SMOKE PASS on this emulator; Bluetooth/iOS NOT TESTED."
