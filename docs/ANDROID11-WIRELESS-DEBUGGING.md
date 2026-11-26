# Android 11 (API 30) Wireless Debugging — iTell 1.6 Build 49

**Status:** open investigation, not a confirmed fix. Android 11 was enabled experimentally by altering the APK manifest `minSdkVersion` from 31 to 30. The original source targets API 31+; full API30 runtime and Wireless Debugging support has **not** yet been verified.

## Reproduce without Android Studio

1. Connect the Android phone to a working Wi-Fi network. Don't attempt to use mobile data alone. Approve the **Allow wireless debugging on this network** prompt in Android Developer options.
2. Go to **Developer options → Wireless debugging**, switch it on, then tap **Pair device with pairing code**.
3. Keep the **six-digit-code dialog open**. On the *same* phone, input the displayed code into iTell using its expanded ongoing pairing notification; if that is hidden/closed, use **split-screen** with Settings and iTell side by side. Avoid closing the pairing dialog or switching Wi-Fi during the attempt; obtain a fresh code if it closes.
4. After the attempt, check Developer options → Wireless debugging → **Paired devices** for `iTell@<model>`. If it appears but audio service is not ready, the failure may be the separate connection to `_adb-tls-connect._tcp` rather than the six-digit pairing.
5. On Android iTell, open **Settings → Advanced (پیشرفته) → Copy log (کپی گزارش)** after reproducing. Review it locally and share **only redacted** lines containing `pairing:`, `mdns`, `Wireless debugging`, `port probe:`, `Shell` and nearby errors. Do **not** share tokens, pairing code, private keys, QR, IP addresses, phone numbers, or personal data. Do **not** press **Send diagnostic log**, as the previous backend/domain is untrusted.

## Source evidence

The decompiled Build49 `defpackage/E9.i()` discovers `_adb-tls-pairing._tcp` via `defpackage/O.r()` using Android `NsdManager` for up to 10 seconds, then calls `defpackage/Lc.F()` for authenticated ADB pairing. A fallback local-port scan exists if the mDNS record is not found. The code reports **wrong pairing code**, **no dialog/port**, and **generic failed** states separately. After successful pairing, `defpackage/C0011aa` independently discovers the `_adb-tls-connect._tcp` port to start Shell. BLE/iOS connection is a separate subsystem.

Android 11 and later support wireless ADB on supported firmware; mDNS and an active Wi-Fi network are prerequisites for this discovery approach.

## CI findings

The first API30 workflow [45878026164](https://github.com/Rasoul-Ketabi/mytell/actions/runs/45878026164) was **cancelled**, not successful. Its logs show `adb install` **Success**, then `adb shell am start -W` hung until cancellation. This does not establish a Wireless Debugging bug by itself or prove the app launched successfully. A follow-up [bounded diagnostic workflow](../.github/workflows/android11-dev.yml) adds explicit timeouts and captures launch/foreground status and logcat rather than hanging indefinitely.

**No new DEX or pairing-protocol workaround has been applied without error evidence.** Never fake a paired/audio-ready state or bypass ADB authentication. Preserve iOS 1.6 QR/BLE protocol and block the lost former domain at network level during tests.
