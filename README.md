# iTell Android Recovery

This repository is reserved for recovering and testing the **Android iTell 1.4 (Build 40)** application against the **existing iTell iOS 1.3** client. The iOS application must remain unchanged.

## Current status

- The original Android Studio source and release signing keystore were lost.
- An original Android APK is available for controlled binary analysis and reconstruction.
- Login and commercial licensing are intended to be **temporarily absent** in the development edition.
- **All access to the legacy `itellapp.com` domain and its subdomains is prohibited**. This includes updates, support links, logging, authentication, and runtime connections.
- Bluetooth pairing, QR payload, key agreement, encrypted transport, calls, and messaging must remain protocol-compatible with iOS 1.3.
- **This repository is currently PUBLIC. No original APK, recovered proprietary sources, signing material, secrets, or test-user data should be committed until the repository has been made PRIVATE.**

## Planned Android CI

Once the repository becomes private, stage the recovery input and the offline patching scripts. The workflow will:
1. SHA-256-pin the original input APK and verify patch preconditions.
2. Build a candidate using official Android SDK build tools (`zipalign`, then `apksigner`).
3. Verify Android resource alignment, DEX integrity, signature, ABI compatibility, and known legacy-domain references.
4. Attempt an ADB installation and startup smoke test using a compatible Android environment.
5. Store output in **private workflow artifacts**, not public Releases. Successful packaging alone is not proof of installation, iPhone pairing, call audio, or security.

**Important:** This is not yet an Android Studio/Gradle source project. The first objective is a reproducible, installable recovery build; maintainable source reconstruction comes later.

## Next action

In GitHub: **Settings → General → Danger Zone → Change repository visibility → Make private**.

Once GitHub reports `private`, the original recovery APK and source-controlled CI can be staged. Do not make a public release of any candidate at this stage.
