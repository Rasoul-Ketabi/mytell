# iTell security / recovery policy

## No trust in old infrastructure

The former `itellapp.com` and `api.itellapp.com` domains, plus all their subdomains, are not owned by this project. They must not be accessed by recovered builds through login, licensing, updates, telemetry, support screens, browser intents, or any other network path.

A static APK string replacement alone is NOT proof of this invariant. Block these domains at network level during controlled testing and inspect actual runtime traffic. Do not treat `offline.test` as a functioning server.

## Core pairing security

Preserve all iTell iOS 1.3 wire-level QR/BLE pairing, ECDH and AES-GCM, session replay protection, certificate requirements, and Android component trust boundaries. Removing commercial account licensing must not silently disable link/device authentication. The recovered native/Shell voice components may retain a separate commercial license gate.

## Public repository

The owner explicitly selected a public repository for this recovery exercise. An original APK in Git history will be publicly available and may contain historical proprietary logic and the obsolete URLs. Do not commit signing secrets, private certificates, authentication tokens, personal data, diagnostic logs, or live account data.

## Accuracy of CI

A cryptographically signed, zipaligned APK is not proven installable until an ADB installation succeeds. A green emulator smoke test is not proof that Bluetooth/iOS pairing, calls or SMS work on actual devices. Release publication is disabled until the owner separately authorizes a reviewed release.
