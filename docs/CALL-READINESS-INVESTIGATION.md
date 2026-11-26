# Call readiness investigation — Build #6

**Date:** 2026-11-26  
**Input:** original iTell Android 1.4 Build 40 APK, SHA-256 `ea715b2f6e254dbd6083ed1338f10dc0845b725e561ab33b47e91d9df5f05ca7`  
**Comparison:** exact Build #6 artifact from Actions run 45477969314  
**Decompilation:** JADX 1.5.7, static analysis of original and Build #6

## User-observed symptom

- Existing iTell iOS 1.3 Settings shows the Android Samsung A14 as `Connected · Encrypted` and displays its model, Android version, battery and carrier.
- The iOS Calls/dialer screen still displays `To use iTell, open it on your Android phone.`
- Owner confirms the Android iTell app was open in the foreground and itself showed Connected.
- Android Studio is currently unavailable to the owner.

## Confirmed Android protocol facts

1. The successful encrypted BLE pairing path is in `defpackage/C0158n1`. After verification it:
   - sends `AbstractC0104i7.e(bridgeService.n, bridgeService.m)` (message type `status`, with `audio` boolean and `err` reason),
   - sends `AbstractC0104i7.e(...)` status again after connection state handling,
   - calls `BridgeService.U()`, which sends `device` details (model, OS, carrier, battery and charging),
   - calls `BridgeService.Y()`, which sends a separate `service` message with `ok`.
   This matches the fact that the iPhone can show encrypted connection and Android device details while its dialer still reports unavailable.

2. The audio/Shell readiness path is separate from BLE pairing:
   - `BridgeService.onCreate()` checks `C0221s8.a()` (whether an `IShellTap` Binder is alive).
   - If the Shell Binder is not alive, it starts the setup/start path via `C0254v8.f(context, "bridge start")` and reports `audio=false` plus the reason from `C0287y8.n()`.
   - `C0287y8.n()` returns concrete readiness states: `turned off`, `setup needed`, `wifi needed`, `wireless debugging off` / `wireless debugging not allowed on this network`, `starting`, `ready`, or `service not running`.
   - The Shell setup uses Android Wireless debugging / ADB pairing and a separately started Shell service. It is not the same connection as the encrypted BLE link.
   - The Android app already contains Settings pages named `audio_title` and `shellinfo_title`; Persian resources label the latter `آی تل روی این گوشی چه کارهایی می‌کند`, with the action `راه‌اندازی صحبت روی آیفون`.

3. Build #6 license bypass facts:
   - `BridgeService.p()` returns true in Build #6 (the original license gate).
   - `C0223t.t()` initializes account state to `EnumC0212s.d` (active) in Build #6.
   - `C0223t.B()` is a no-op in Build #6 (suppresses old online account-state transitions).
   - Therefore the remaining Shell readiness state is an independent prerequisite; it is not bypassed by the account/license patch.

## Most likely explanation (not yet runtime-confirmed)

The encrypted BLE transport is working, but the Android Shell/Call-Audio subsystem has not reached `ready`. Android can therefore show Connected while iOS still treats call/audio use as unavailable. The iOS source is not available, so the exact mapping of its English warning to the Android `status.audio` field cannot be proven from Android APK alone; however, the Android protocol clearly sends a distinct audio readiness status and reason.

A second independent possibility is an expired stored link certificate: `BridgeService.Y()` sets `service.ok = p() && (linkCert == null || now < linkCert.exp)`. This must be considered if the Shell status is ready but the iOS warning persists. Do not weaken pairing encryption or invent certificates.

## No code patch applied in this investigation

No new DEX patch was made because marking audio ready without a working Shell Binder would falsely advertise call capability and likely produce failed calls. First inspect the existing Android UI status.

## Owner-side check (no Android Studio or PC required)

On the Android phone, open iTell and go to **Settings → Talking on the iPhone / آی تل روی این گوشی چه کارهایی می‌کند** (also inspect **Settings → Call Audio / صدای تماس**).

Check the displayed state:
- `صحبت روی آیفون روشن است` / `Talking on the iPhone is on` indicates Shell service is running.
- `صحبت روی آیفون الان فعال نیست` / `Talking on the iPhone isn't running right now`, `راه‌اندازی نشده`, `اشکال‌زدایی بی‌سیم خاموش است`, or `در انتظار Wi-Fi` indicates which setup step remains.
- If not running, use **راه‌اندازی صحبت روی آیفون / Set Up Talking on the iPhone** and complete the in-app Wireless debugging pairing/setup wizard. This can be done directly on the Android phone; Android Studio is not required.

After Shell says it is running, reopen the iOS app and check Calls again. If it still warns, obtain the Android app's built-in diagnostic log/status (redact phone numbers, QR secrets and keys) so the remaining `service.ok` / certificate condition can be investigated.

## Acceptance criteria

- iOS 1.3 continues to pair without changes.
- Android shows BLE Connected + Encrypted.
- Shell/Call-Audio state is genuinely ready (not merely forced true).
- iOS Calls screen no longer reports Android unavailable.
- Real outgoing/incoming calls and two-way audio are tested separately.
- Old domains remain blocked at network level; no security/certificate trust is forged.
