# iTell Android recovery status — 24 November 2026

## Goal
Create an installable development Android APK compatible with the already installed **iTell iOS 1.3** app, without old online account/licensing and without network calls to the former, untrusted domain.

## Verified GitHub Actions run

[Recovery build #6 (run 45477969314)](https://github.com/Rasoul-Ketabi/mytell/actions/runs/45477969314) — **success**.

- Input APK (4,189,976 bytes) has SHA256 `ea715b2f6e254dbd6083ed1338f10dc0845b725e561ab33b47e91d9df5f05ca7` and original DEX SHA pinned.
- Three experimental commercial-gate patch locations applied with exact original-byte preconditions.
- Official Android SDK `zipalign` completed and verified.
- Official SDK `apksigner` signed APK using **ephemeral per-run dev certificate** and signature verified.
- Independent ZIP LOCAL-header `resources.arsc` 4-byte alignment validation passed (the earlier verifier incorrectly read CENTRAL directory extra length; fixed).
- Static checks for old ASCII/UTF16 domain literals and DEX checksums passed. **Not a proof of total runtime network safety.**
- **Android API 35 x86_64 Google APIs emulator ADB install succeeded:** `Performing Streamed Install\nSuccess`.
- Package `com.itellapp.android` was visible to `adb shell pm path`.
- Launcher smoke test executed; no crash signature was found during the short log inspection, and output says `INSTALL AND LAUNCH SMOKE PASS`.

Download: [Build #6 signed APK artifact](https://github.com/Rasoul-Ketabi/mytell/actions/runs/45477969314/artifacts/14960176916). Artifact retention is 14 days.

Diagnostics: [Build #6 emulator logs artifact](https://github.com/Rasoul-Ketabi/mytell/actions/runs/45477969314/artifacts/14959434934).

## Important limitations

- This is a patched APK, NOT restored Android Studio source.
- Neither normal Android UI navigation nor BLE pairing to iTell iOS 1.3 have been tested.
- Commercial licensing logic in Shell/native audio and possible server-signed pairing certificate dependencies may still prevent features.
- Literal domain replacement alone cannot guarantee no dynamically constructed or WebView/intent-originated requests to the lost domain; use DNS/firewall blocking in an isolated test network.
- A new ephemeral signing identity is generated each run: uninstall any previously installed iTell APK before installing a new build (app data will be lost). **Never publish a throwaway signer as an update to existing installed builds.**
- The emulator may differ from actual Android vendor phones and does not validate Bluetooth/iOS integration.
- The existing iOS 1.3 app must not be changed.

## Next validation

Install the Build #6 APK on a dedicated Android test phone (Android 12+, compatible ABI) with old domains blocked. Verify app launch and QR display before pairing to the existing iOS 1.3 app. Preserve ADB logcat if a crash or pairing failure occurs. Do not use real accounts, personal SMS, or sensitive SIM data in these tests.
