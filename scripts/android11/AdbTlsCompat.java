package com.itellapp.android.compat;

import android.net.ssl.SSLSockets;
import android.os.Build;
import java.security.NoSuchAlgorithmException;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLException;
import org.conscrypt.Conscrypt;

/** Keep authenticated ADB TLS provider local to this connection; never install globally. */
public final class AdbTlsCompat {
    private AdbTlsCompat() {}

    public static SSLContext getContext(String protocol) throws NoSuchAlgorithmException {
        if (Build.VERSION.SDK_INT >= 31) {
            return SSLContext.getInstance(protocol);
        }
        return SSLContext.getInstance(protocol, Conscrypt.newProvider());
    }

    public static byte[] exportKeyingMaterial(SSLSocket socket, String label,
                                              byte[] context, int length) throws SSLException {
        if (Build.VERSION.SDK_INT >= 31) {
            return SSLSockets.exportKeyingMaterial(socket, label, context, length);
        }
        if (!Conscrypt.isConscrypt(socket)) {
            throw new SSLException("ADB TLS socket is not backed by bundled Conscrypt");
        }
        byte[] key = Conscrypt.exportKeyingMaterial(socket, label, context, length);
        if (key == null || key.length != length) {
            throw new SSLException("ADB TLS exporter returned an invalid key");
        }
        return key;
    }
}
