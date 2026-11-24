# iTell recovery security policy

## Trust boundary

The former production domains `itellapp.com` and `api.itellapp.com`, including subdomains, are **not owned by the project** and must be treated as untrusted.

- Never request authentication, licensing, updates, telemetry, or support endpoints on the former domains.
- Keep domain blocks in test DNS/firewall **even if static APK scans report no matches**.
- Validate all outbound connection paths, including WebView intents, native libraries, redirected connections, and dynamically assembled URLs, before installing on non-isolated devices.
- Preserve QR/BLE pairing protocol compatibility with the **already-installed iTell iOS 1.3** client; do not substitute fake security credentials for required device authentication.
- Licensing removal in Development Edition must not disable secure pairing, session encryption, replay protection, or Android component authentication.

## Repository

This repository is currently public; no recovered APK, proprietary assets, private keystore, credentials, source dump, private user data, or signed build candidates belong here until it is made private.
All signing credentials must remain in encrypted CI secrets or outside GitHub, never in version control or logs.

## Build acceptance

A ZIP integrity check, cryptographic APK signature and zipalign verify are **not enough**. To call a build installable we must also see a successful installation/launch test on a compatible Android environment. Pairing, BLE wake, calls, SMS, and audio must be tested with iTell iOS 1.3 on real devices.
