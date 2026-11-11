# Android OpenSDK Integration (Dahua / Lechange / Imou)

This module provides the Android native bridge and error handling layer for Molido CCTV AI platform, based on **Android OpenSDK Development Guide V3.8.0**.

## 1. Prerequisites and Library Files
Place the following files from your vendor distribution into the app module:
- `libs/OpenApiClient.jar`
- `libs/OpenSDK.jar`
- `src/main/jniLibs/{armeabi-v7a, arm64-v8a}/libOpenSDK.so`
- `src/main/jniLibs/{armeabi-v7a, arm64-v8a}/libOpenApiClient.so`

## 2. Permissions Required (`AndroidManifest.xml`)
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
<uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

## 3. Error Handling and Resolution Matrix
The `OpenSDKErrorResolver.kt` automatically maps vendor error codes to recovery workflows:
- **`STATE_RTSP_AUTHORIZATION_FAIL` (401)**: Prompts user to renew device credentials or re-authenticates token.
- **`STATE_RTSP_SERVICE_UNAVAILABLE` (503)**: Camera maximum connections reached. The client automatically downgrades to the sub-stream (`subType=1`) to conserve hardware resources.
- **`STATE_DHHTTP_SERVER_ERROR` (503001)**: Cloud disconnect. Triggers P2P hole punching reconnection or LAN direct RTSP fallback.
- **`DEC_KEY_ERROR` (403002)**: Hardware stream encryption active. Requests device safety code from operator.
- **`BLUETOOTH_DISABLED` (1001)**: Prompts user to activate BLE adapter for door access.
