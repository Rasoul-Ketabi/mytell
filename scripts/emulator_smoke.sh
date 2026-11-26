#!/usr/bin/env bash
set -euo pipefail
APK="${1:-dist/itell-dev.apk}"
PKG="com.itellapp.android"
mkdir -p smoke-logs

adb devices -l | tee smoke-logs/devices.txt
adb shell getprop ro.product.cpu.abilist | tee smoke-logs/abis.txt

if ! adb install -r "$APK" > smoke-logs/install.txt 2>&1; then
  cat smoke-logs/install.txt
  adb logcat -d -t 500 > smoke-logs/logcat-install.txt 2>&1 || true
  echo "INSTALL FAILED. Check ABI vs APK native libraries." >&2
  exit 1
fi
cat smoke-logs/install.txt

adb shell pm path "$PKG" | tee smoke-logs/package.txt
grep -q "package:" smoke-logs/package.txt

# Resolve the actual launcher activity and explicitly start it; a monkey event
# alone is not sufficient proof that the app entered the foreground.
ACTIVITY="$(adb shell cmd package resolve-activity --brief \
  -a android.intent.action.MAIN -c android.intent.category.LAUNCHER "$PKG" \
  | tr -d '\r' | tail -n1)"
printf '%s\n' "$ACTIVITY" | tee smoke-logs/launcher-activity.txt
case "$ACTIVITY" in
  "$PKG/"*) ;;
  *) echo "No launcher activity resolved for $PKG" >&2; exit 1 ;;
esac

adb logcat -c || true
if ! adb shell am start -W -n "$ACTIVITY" > smoke-logs/launch.txt 2>&1; then
  cat smoke-logs/launch.txt
  adb logcat -d -t 1200 > smoke-logs/logcat-launch.txt 2>&1 || true
  exit 1
fi
cat smoke-logs/launch.txt
grep -Eq 'Status: ok|Activity: ' smoke-logs/launch.txt

sleep 7
adb shell pidof "$PKG" | tee smoke-logs/process.txt
test -s smoke-logs/process.txt

adb shell dumpsys activity activities > smoke-logs/activities.txt
grep -E 'mResumedActivity|topResumedActivity' smoke-logs/activities.txt \
  | tee smoke-logs/resumed-activity.txt
grep -Fq "$PKG" smoke-logs/resumed-activity.txt

adb logcat -d -t 1600 > smoke-logs/logcat-launch.txt 2>&1 || true
if grep -Ei "FATAL EXCEPTION|Process: $PKG" smoke-logs/logcat-launch.txt > smoke-logs/crash-matches.txt; then
  echo "Crash signature found in launch logs." >&2
  cat smoke-logs/crash-matches.txt
  exit 1
fi
echo "INSTALL + RESOLVED LAUNCH + LIVE PROCESS + FOREGROUND ACTIVITY PASS; Bluetooth/iOS NOT TESTED."
