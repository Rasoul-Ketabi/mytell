#!/usr/bin/env bash
# Build iTell 1.6 Build49 Android 11 experimental TLS-compatible APK.
# Run on GitHub-hosted Ubuntu with Android build-tools 36 and platform android-36.
set -euo pipefail
umask 077
WORK="${RUNNER_TEMP:-/tmp}/itell-api30-tls"
mkdir -p "$WORK/tools" "$WORK/conscrypt" "$WORK/helper-classes" "$WORK/dex" dist
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
BT="$SDK/build-tools/36.0.0"
PLATFORM="$SDK/platforms/android-36/android.jar"
[[ -f "$PLATFORM" ]] || { echo 'Missing Android platform 36' >&2; exit 1; }
[[ -x "$BT/d8" && -x "$BT/zipalign" && -x "$BT/apksigner" ]] || { echo 'Missing Android build tools 36' >&2; exit 1; }

python3 scripts/prepare_dev_apk_16.py \
  --source inputs/itell-1.6-49.apk \
  --output "$WORK/unsigned31.apk" \
  --report dist/recovery-report.json
python3 scripts/prepare_android11_compat.py \
  --input "$WORK/unsigned31.apk" \
  --output "$WORK/unsigned30.apk" \
  --report dist/android11-manifest-report.json

SMALI_VERSION=3.0.10
SMALI_BASE="https://github.com/baksmali/smali/releases/download/${SMALI_VERSION}"
curl --fail --location --retry 3 --silent --show-error \
  "$SMALI_BASE/baksmali-${SMALI_VERSION}-fat-release.jar" -o "$WORK/tools/baksmali.jar"
curl --fail --location --retry 3 --silent --show-error \
  "$SMALI_BASE/smali-${SMALI_VERSION}-fat-release.jar" -o "$WORK/tools/smali.jar"
printf '%s  %s\n' \
  '37ae4a41a8886e15c20b8362fa4250f96bbdb55e1a608199ad8b5dff068b588f' "$WORK/tools/baksmali.jar" \
  '32fa0e88a6c397b3922201adf5f3e534fbaed5a663c71d0c558c3ddce0af844a' "$WORK/tools/smali.jar" \
  | sha256sum --check

CONSCRYPT_VERSION=2.5.3
CONSCRYPT_URL="https://repo.maven.apache.org/maven2/org/conscrypt/conscrypt-android/${CONSCRYPT_VERSION}/conscrypt-android-${CONSCRYPT_VERSION}.aar"
curl --fail --location --retry 3 --silent --show-error "$CONSCRYPT_URL" -o "$WORK/conscrypt.aar"
curl --fail --location --retry 3 --silent --show-error "${CONSCRYPT_URL}.sha1" -o "$WORK/conscrypt.aar.sha1"
EXPECTED_SHA1="$(sed -n 's/^\([a-fA-F0-9]\{40\}\).*$/\1/p' "$WORK/conscrypt.aar.sha1" | head -n1)"
[[ ${#EXPECTED_SHA1} -eq 40 ]] || { echo 'Invalid official Conscrypt SHA1 metadata' >&2; exit 1; }
echo "$EXPECTED_SHA1  $WORK/conscrypt.aar" | sha1sum --check
unzip -q "$WORK/conscrypt.aar" classes.jar -d "$WORK/conscrypt"

javac -source 8 -target 8 -cp "$PLATFORM:$WORK/conscrypt/classes.jar" \
  -d "$WORK/helper-classes" scripts/android11/AdbTlsCompat.java
jar cf "$WORK/helper.jar" -C "$WORK/helper-classes" .
"$BT/d8" --min-api 30 --lib "$PLATFORM" --output "$WORK/dex" \
  "$WORK/helper.jar" "$WORK/conscrypt/classes.jar"

python3 scripts/android11/tls30_qr_repack.py \
  --input "$WORK/unsigned30.apk" \
  --output "$WORK/unsigned-tls30.apk" \
  --report dist/tls30-qr-report.json \
  --smali "$WORK/tools/smali.jar" \
  --baksmali "$WORK/tools/baksmali.jar" \
  --conscrypt-aar "$WORK/conscrypt.aar" \
  --compiled-dex "$WORK/dex"

"$BT/aapt" dump badging "$WORK/unsigned-tls30.apk" | tee dist/badging.txt
grep -Fq "sdkVersion:'30'" dist/badging.txt
grep -Fq "targetSdkVersion:'36'" dist/badging.txt
"$BT/zipalign" -P 16 -f -v 4 "$WORK/unsigned-tls30.apk" "$WORK/aligned.apk" > dist/zipalign.txt
"$BT/zipalign" -c -P 16 -v 4 "$WORK/aligned.apk" >> dist/zipalign.txt
keytool -genkeypair -noprompt -storetype PKCS12 \
  -keystore "$WORK/dev-signer.p12" \
  -storepass 'itell-test-only' -keypass 'itell-test-only' \
  -alias itell-dev -keyalg RSA -keysize 3072 -validity 3650 \
  -dname 'CN=iTell API30 experimental test,O=iTell,C=US'
export SIGNPASS='itell-test-only'
"$BT/apksigner" sign \
  --ks "$WORK/dev-signer.p12" --ks-type PKCS12 \
  --ks-key-alias itell-dev --ks-pass env:SIGNPASS --key-pass env:SIGNPASS \
  --v1-signing-enabled false --v2-signing-enabled true \
  --v3-signing-enabled true --v4-signing-enabled false \
  --out dist/iTell-1.6-B49-Android11-TLS30-QR-RECOVERY-DEV.apk "$WORK/aligned.apk"
"$BT/apksigner" verify --verbose --print-certs --min-sdk-version 30 \
  dist/iTell-1.6-B49-Android11-TLS30-QR-RECOVERY-DEV.apk | tee dist/signature.txt
"$BT/zipalign" -c -P 16 -v 4 dist/iTell-1.6-B49-Android11-TLS30-QR-RECOVERY-DEV.apk > dist/signed-zipalign.txt
python3 scripts/verify_apk.py dist/iTell-1.6-B49-Android11-TLS30-QR-RECOVERY-DEV.apk | tee dist/static-checks.json
sha256sum dist/iTell-1.6-B49-Android11-TLS30-QR-RECOVERY-DEV.apk | tee dist/apk-sha256.txt
printf '%s\n' 'APK constructed. Secure pairing with a physical Android11 and iPhone not yet verified.'
