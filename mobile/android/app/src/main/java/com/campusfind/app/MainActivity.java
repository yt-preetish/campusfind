package com.campusfind.app;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    @Override
    public void onBackPressed() {
        // Let Capacitor handle back button
        if (getBridge() != null) {
            getBridge().getWebView().evaluateJavascript(
                "window.history.back();",
                null
            );
        } else {
            super.onBackPressed();
        }
    }
}
