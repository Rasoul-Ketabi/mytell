#!/usr/bin/env bash
# API 30 probe: bounded launch with useful logs even if app deadlocks on start.
set -euo pipefail
APK="${1:?APK required}"
PKG=com.itellapp.android
mkdir -p smoke-logs
{
  adb devices -l
  adb shell getprop ro.build.version.sdk
  adb shell getprop ro.product.cpu.abilist
} | tee smoke-logs/device-info.txt
if ! timeout -k 5s 60s adb install -r "$APK" > smoke-logs/install.txt 2>&1; then
  cat smoke-logs/install.txt
  timeout 10s adb logcat -d -t 800 > smoke-logs/logcat-install.txt 2>&1 || true
  echo "Android 11 install failure (or timeout)" >&2
  exit 1
fi
cat smoke-logs/install.txt
grep -Fq "Success" smoke-logs/install.txt
timeout 15s adb shell pm path "$PKG" | tee smoke-logs/package.txt
grep -Fq "package:" smoke-logs/package.txt
ACTIVITY="$(timeout 20s adb shell cmd package resolve-activity --brief   -a android.intent.action.MAIN -c android.intent.category.LAUNCHER "$PKG" | tr -d '\r' | tail -n 1)"
printf '%s\n' "$ACTIVITY" | tee smoke-logs/launcher-activity.txt
case "$ACTIVITY" in "$PKG/"*) ;; *) echo "Launcher resolution failed" >&2; exit 1 ;; esac

timeout 12s adb logcat -c || true
# Android 11 on a headless emulator can block indefinitely waiting for
# window-drawn in 'am start -W'. Bound it so the CI produces actionable logs.
set +e
timeout -k 5s 40s adb shell am start -W -n "$ACTIVITY" > smoke-logs/launch.txt 2>&1
LAUNCH_RESULT=$?
set -e
echo "am_start_exit_code=$LAUNCH_RESULT" | tee smoke-logs/launch-status.txt
cat smoke-logs/launch.txt

sleep 7
timeout 10s adb shell pidof "$PKG" > smoke-logs/process.txt 2>&1 || true
timeout 12s adb shell dumpsys activity activities > smoke-logs/activities.txt 2>&1 || true
timeout 15s adb logcat -d -t 2200 > smoke-logs/logcat-launch.txt 2>&1 || true

cat smoke-logs/process.txt
grep -E 'mResumedActivity|topResumedActivity' smoke-logs/activities.txt | tee smoke-logs/resumed-activity.txt || true
if grep -Ei "FATAL EXCEPTION|Process: $PKG|NoSuchMethodError|NoSuchFieldError|VerifyError|NoClassDefFoundError"   smoke-logs/logcat-launch.txt > smoke-logs/crash-matches.txt; then
  cat smoke-logs/crash-matches.txt >&2
  exit 1
fi
if ! grep -Fq "$PKG" smoke-logs/resumed-activity.txt; then
  echo "Android 11 app not foreground (am start result: $LAUNCH_RESULT)" >&2
  exit 1
fi
if ! test -s smoke-logs/process.txt; then
  echo "Android 11 app process is not alive" >&2
  exit 1
fi
echo "API30 INSTALL, PROCESS AND FOREGROUND PASS (am start exit code: $LAUNCH_RESULT); pairing/audio not tested"
