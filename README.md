# iTell Android recovery — current baseline: 1.6 Build 49

> **Current baseline:** [original Android 1.6 Build 49 APK](inputs/itell-1.6-49.apk) is now uploaded and its exact SHA-256 has been verified. Build 49 CI packaging and the stricter Android API 35 emulator install/foreground-launch checks have passed. The old `downloads/Build-6` APK is historical and based on Android 1.4 Build 40.

The target is compatibility with **iTell iOS 1.6**, temporarily bypassing the online commercial account/license checks while preserving QR/BLE security. The [Build 49 CI workflow](.github/workflows/android-dev-16.yml) and [Build 49 recovery script](scripts/prepare_dev_apk_16.py) are active. Source APK SHA-256: `aab15e238a168607eccf05547e88aee69d91ddb71283c9fb3dd3112c55e86a03`.

**Current validation:** three DEX patches applied with exact byte preconditions; 55 explicit old-domain literals replaced; official Android SDK zipalign and apksigner steps succeeded; DEX integrity and ZIP alignment checks passed. Android API 35 ADB installation, launcher resolution, explicit activity start, live process, and foreground activity are verified. iOS 1.6 pairing, calls/audio, full commercial-gate removal, and runtime network isolation are not yet confirmed. Literal replacement does not prove that no dynamically constructed request can reach the former domain.

**Download:** [Build 49 DEV APK](downloads/iTell-Android-1.6-b49-DEV-UNVERIFIED-PAIRING.apk). Each CI run creates a new ephemeral test certificate; uninstall any previous iTell DEV build before installing a newer one. This is not a production or public release.

## Android OS compatibility

**IMPORTANT:** The source and signed DEV Android 1.6 Build 49 APK both declare `minSdkVersion=31`, meaning **Android 12 or later is required**. The target SDK is 36. **Android 11 (API 30) cannot install the current Build 49 APK**, even if Google Play Protect is disabled. Prior successful GitHub CI installation on Android 15 (API 35) does not establish Android 11 support. A separately built and thoroughly tested Android 11 compatibility variant would be necessary; merely changing the manifest number is not sufficient proof that Android 12-only APIs are absent.

## Historical Build 40 notes

[GitHub Actions](https://github.com/Rasoul-Ketabi/mytell/actions)

This is an experimental reconstruction from **Android APK 1.4 Build 40**, **not original Android Studio source code**.

**Primary goal:** recover an installable Android app that can pair with the already installed **iTell iOS 1.6** app without changing its code. Temporarily remove the old commercial account/license requirement while preserving secure QR/BLE/Wi-Fi pairing and telephony.

## Security and visibility

**This repository is PUBLIC by the project owner's explicit choice.** Do not publish any private key, keystore, token, password or user data.

The former domains `itellapp.com` and `api.itellapp.com` are no longer owned by the project and must be treated as hostile. The recovery script replaces explicit occurrences of the old domain with the reserved `offline.test` name; that substitution does NOT prove dynamic network safety. Before testing, independently block the old domains in DNS/firewall. Do not run an unreviewed APK with real accounts or sensitive SIM data.

## Bootstrapping the recovery build

**One original input is required:** `inputs/itell-1.4-b40-original.apk`.

1. Get the exact historical APK from the project owner's archival copy (4,189,976 bytes).
2. Upload it to `inputs/itell-1.4-b40-original.apk` in this repository. Because the repo is public, that binary and its original legacy server URLs become public too. Never upload signing secrets.
3. The `iTell Android - DEV recovery and install test` GitHub Actions workflow triggers automatically on the commit, or use **Actions → Run workflow**.
4. The job checks the original APK digest, applies the small binary patch, uses official Android SDK tools `zipalign` and `apksigner`, verifies DEX/resource structure and attempts ADB install and launch using Android API 35.
5. If all jobs pass, download `itell-dev-package-<run_number>` from that run's **Artifacts**. There is intentionally no GitHub Release yet.

**SHA-256 required for the input:** `ea715b2f6e254dbd6083ed1338f10dc0845b725e561ab33b47e91d9df5f05ca7`

## What a green job means — and does not mean

A green package job establishes correctly aligned and cryptographically signed packaging for the checked APK and a static old-domain literal scan. A green emulator job establishes installation and launch on **that** emulator only. Neither proves security, ability to pair with iPhone, voice calling or broad handset compatibility.

The APK has ARM-only native libraries. ABI translation in x86_64 API 35 emulators is device-image-specific. If `INSTALL_FAILED_NO_MATCHING_ABIS` occurs, diagnose the actual emulator architecture; do **not** claim the APK is generically un-installable.

The workflow uses a new throwaway signing certificate per run. You must uninstall any previously installed iTell package with a different signer before installing a new candidate. This erases local app data.

**Never modify the original iOS 1.3 app for these tests.** Do not disable secure pairing/crypto merely to bypass commercial licensing.

Detailed status: [docs/RECOVERY-STATUS.md](docs/RECOVERY-STATUS.md) and [docs/SECURITY.md](docs/SECURITY.md).
