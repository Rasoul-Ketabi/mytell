# iTell Android recovery status — 24 November 2026

## Goal
Create an installable development Android APK that is compatible with the already-installed iTell iOS 1.3 app, without any commercial login or online licensing dependency and without communication with the old, untrusted domains.

## Source constraints
- Original Android Studio sources and the former signing keystore are lost.
- `itell-1.4-40.apk` is the sole original compiled recovery input.
- The previous experimental APKs failed installation in Android Studio / emulators, including an Android 11+ `resources.arsc` alignment failure.
- Existing iOS binary must not change.

## Implemented in this repository
- Source APK SHA256 and DEX SHA256 pinning.
- Carefully preconditioned three-location experimental DEX patch.
- Byte-preserving length-matched substitutions of literal legacy domain references in APK entries.
- DEX checksum recomputation.
- Offline Android SDK `zipalign` -> `apksigner` -> `verify` workflow.
- Static verification of resource alignment, DEX checksums, and explicit old-domain bytes.
- Separate emulator installation/launch test. Failure remains a failure.
- Per-build ephemeral test signing. A prior APK must be uninstalled before installing one signed by another temporary key.

## Not yet verified
- Running the build on GitHub Actions (original input binary has not been uploaded to the repository).
- Real-device installation.
- Secure QR/BLE pairing with iOS 1.3.
- Link certificate validation without the former server.
- Shell audio and call operation.
- Absence of every dynamically constructed network request to the legacy domains; literal substitution alone is **not** a sufficient runtime guarantee.

## Publication constraints
APK builds are CI artifacts with explicit `untested` naming. No release is automatically published. Public repository access means CI artifacts and all committed inputs may be publicly visible.

## Next concrete action
Upload the original 4,189,976-byte APK at `inputs/itell-1.4-b40-original.apk`. The SHA256 guard will reject a mistaken or modified file. Once committed, review the GitHub Actions run and correct any deterministic failure before re-running it.
