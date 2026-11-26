# iTell Android recovery — current baseline: 1.6 Build 49

> **Current test candidate: [download APK 1.6 Build 49 from this conversation](https://github.com/Rasoul-Ketabi/mytell/tree/main/inputs).** The new source APK has **not yet** been uploaded to this repository; the linked folder is the staging location, not a finished Build 49 binary. The existing `downloads/Build-6` APK is **historical** and based on Android 1.4 Build 40; do not confuse it with Build 49.

The current target is compatibility with **iTell iOS 1.6**, without online account/licensing and with every reference to the lost legacy domain eliminated. A separate [Build 49 CI workflow](.github/workflows/android-dev-16.yml) and [Build 49 recovery script](scripts/prepare_dev_apk_16.py) are present. Upload `inputs/itell-1.6-b49-original.apk` (SHA-256 `aab15e238a168607eccf05547e88aee69d91ddb71283c9fb3dd3112c55e86a03`) to activate Build 49 GitHub tests.

**Testing status:** The locally generated Build 49 APK has passed static DEX, alignment, ZIP and v2 signature checks. It has **NOT** yet been tested by ADB or an iPhone. The prior successful emulator CI installation is for Build 40 **only**.

## Historical Build 40 notes

[GitHub Actions](https://github.com/Rasoul-Ketabi/mytell/actions)

This is an experimental reconstruction from **Android APK 1.4 Build 40**, **not original Android Studio source code**.

**Primary goal:** recover an installable Android app that can pair with the already installed **iTell iOS 1.3** app without changing its code. Temporarily remove the old commercial account/license requirement while preserving secure QR/BLE/Wi-Fi pairing and telephony.

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
