# iTell 1.6 Build 49 — recovery input

Upload the *original, unmodified* APK to this location with the exact file name:

`inputs/itell-1.6-49.apk`

- Expected size: **4,716,760 bytes**
- Required SHA-256: `aab15e238a168607eccf05547e88aee69d91ddb71283c9fb3dd3112c55e86a03`
- DEX SHA-256: `13e658ed9e7633c8cd8d3baf431322157fa4139719e92039e9bbc6390cb5a4ca`

The [Build 49 workflow](../.github/workflows/android-dev-16.yml) automatically packages this input with official Android SDK `zipalign` / `apksigner`, validates it, and attempts ADB installation and a launch smoke test on an Android 15 emulator.

This is a **PUBLIC** repository; the original binary and legacy-domain references it contains will be visible to others. Do not upload signing keys, credentials, personal data or production secrets.

The candidate is for controlled development **only**: iOS 1.6 QR/BLE pairing, calls, audio, complete license removal and runtime network safety are not yet verified.
