# Original recovery input

Upload the exact **original** iTell Android 1.4 Build 40 APK to this directory as:

`inputs/itell-1.4-b40-original.apk`

Expected byte size: **4,189,976 bytes**

Expected SHA-256:
`ea715b2f6e254dbd6083ed1338f10dc0845b725e561ab33b47e91d9df5f05ca7`

The recovery script refuses any APK with a different digest and checks the original DEX SHA-256 separately.

**WARNING**: This original APK has references to the previously owned, now-untrusted domain. Do not install it or use it to access real accounts. Since the repository is PUBLIC, uploading it will publish the original APK to everyone, permanently within Git history. The project owner has explicitly chosen to continue in a public repository. Never upload any signing key, passwords, identity documents, or user data.

CI is intentionally unable to generate an installable candidate until this file is present.
