package com.itellapp.android.compat;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeAdvertiser;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Toast;
import com.itellapp.android.BridgeService;

/**
 * Diagnostic-only. Shows the actual BLE/GATT state during the initial QR wizard.
 * No QR tokens, addresses, public keys or personal information are logged.
 */
public final class BleWizardProbe {
    private static final String TAG = "iTellBLEQR";
    private BleWizardProbe() {}

    private static void notice(final Context context, final String message) {
        Log.i(TAG, message);
        new Handler(Looper.getMainLooper()).post(new Runnable() {
            @Override public void run() {
                Toast.makeText(context.getApplicationContext(), message, Toast.LENGTH_LONG).show();
            }
        });
    }

    public static void onRefresh(BridgeService bridge) {
        try {
            BluetoothManager bm = (BluetoothManager) bridge.getSystemService(Context.BLUETOOTH_SERVICE);
            BluetoothAdapter adapter = bm == null ? null : bm.getAdapter();
            if (adapter == null) {
                notice(bridge, "iTell QR: Bluetooth adapter missing");
                return;
            }
            if (!adapter.isEnabled()) {
                notice(bridge, "iTell QR: Bluetooth is OFF");
                return;
            }
            if (!adapter.isMultipleAdvertisementSupported()) {
                notice(bridge, "iTell QR: BLE peripheral advertising UNSUPPORTED");
                return;
            }
            BluetoothLeAdvertiser advertiser = adapter.getBluetoothLeAdvertiser();
            if (advertiser == null) {
                notice(bridge, "iTell QR: BLE advertiser UNAVAILABLE");
                return;
            }
            if (bridge.b == null) {
                notice(bridge, "iTell QR: GATT server NOT OPEN");
                return;
            }
            notice(bridge, "iTell QR: BLE capable; GATT open; advertising requested");
        } catch (Throwable ex) {
            notice(bridge, "iTell QR: BLE diagnostic error (" + ex.getClass().getSimpleName() + ")");
        }
    }

    public static void onAdvertisingSuccess(Context ctx) {
        notice(ctx, "iTell QR: BLE advertising STARTED; scan QR now");
    }

    public static void onAdvertisingFailure(Context ctx, int code) {
        String reason;
        switch (code) {
            case 1: reason = "DATA_TOO_LARGE"; break;
            case 2: reason = "TOO_MANY_ADVERTISERS"; break;
            case 3: reason = "ALREADY_STARTED"; break;
            case 4: reason = "INTERNAL_ERROR"; break;
            case 5: reason = "FEATURE_UNSUPPORTED"; break;
            default: reason = "ERROR_" + code;
        }
        notice(ctx, "iTell QR: BLE advertising FAILED: " + reason);
    }
}
