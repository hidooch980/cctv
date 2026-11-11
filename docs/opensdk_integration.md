# Dahua / Lechange / Imou OpenSDK Integration Guide

This guide documents the native and backend integration of the **Android OpenSDK V3.8.0** within the Molido CCTV AI ecosystem.

## 1. SDK Architecture & Package Structure
The OpenSDK client uses the modern package namespace `com.open.opensdk` (formerly `com.lechange.opensdk`):
- `OpenApiClient.jar` & `libOpenApiClient.so`: Network communication, P2P protocol, cloud relay.
- `OpenSDK.jar` & `libOpenSDK.so`: Player window management, video decoding (H.264 / H.265), fish-eye lens correction, and audio intercom.

## 2. Core Player Lifecyle (`OpenSDK_PlayWindow`)

```java
// 1. Initialize Player Surface
OpenSDK_PlayWindow.initPlayWindowWithSurface(windowIndex, surfaceView.getHolder().getSurface());

// 2. Set Stream Callback for Status & Error Reporting
OpenSDK_PlayWindow.setStreamCallback(windowIndex, new StreamCallback() {
    @Override
    public void onPlayerResult(int resultSource, int code, String msg) {
        // Dispatched to Molido OpenSDKErrorResolver
        OpenSDKErrorResolver.handlePlayerError(String.valueOf(code), ...);
    }
});

// 3. Start Live Play
OpenSDK_PlayWindow.startRealPlay(deviceSerial, channelId, streamType);
```

## 3. Comprehensive Error Resolution Matrix

| Status / Error Code | Category | Name | Root Cause | Automated Recovery Strategy |
|:---|:---|:---|:---|:---|
| `STATE_RTSP_AUTHORIZATION_FAIL` (401) | RTSP Protocol | Auth Failure | Incorrect camera credentials, expired token | Re-authenticate token, prompt user to update password |
| `STATE_RTSP_SERVICE_UNAVAILABLE` (503) | RTSP Limit | Max Concurrent Streams | Hardware encoder overload, maximum stream connections reached | Automatic fallback to sub-stream (`subtype=1`) |
| `STATE_DHHTTP_SERVER_ERROR` (503001) | Cloud Relay | Relay Server Disconnect | Cloud relay bandwidth limit reached or server timeout | Initiate direct P2P hole-punching or switch to LAN RTSP |
| `DEC_KEY_ERROR` (403002) | Decoder | Decryption Key Mismatch | Device hardware video encryption enabled | Prompt user for camera device safety code (on camera label) |
| `STATE_PACKET_FRAME_ERROR` (502) | Network | Packet Loss / Corruption | Unstable WiFi/LAN, missing video P-frames | Switch transport from UDP to TCP, downgrade bitrate |
| `BLUETOOTH_DISABLED` (1001) | BLE Access | Bluetooth Disabled | OS or user disabled Bluetooth radio | Prompt user with system Bluetooth enable intent |
| `PERMISSION_DENIED` (1002) | BLE Access | Missing Permissions | Missing `BLUETOOTH_SCAN` / `ACCESS_FINE_LOCATION` | Request Android 12+ runtime permissions |
| `GATT_CONNECT_FAILED` (2001) | BLE Access | GATT Connection Failed | Access control reader out of range or busy | Retry BLE scan with exponential backoff |

## 4. Automated Error Remediation API
The Molido backend exposes a dedicated diagnostic endpoint for operators and automated agents:
- **Endpoint**: `POST /api/v1/opensdk/diagnose`
- **Request Body**:
```json
{
  "error_identifier": "503001",
  "camera_id": 1
}
```
- **Response**:
```json
{
  "code": "STATE_DHHTTP_SERVER_ERROR",
  "numeric_code": 503001,
  "category": "DHHTTP Cloud",
  "name": "DHHTTP Cloud Server Disconnect",
  "description_fa": "سرور ابری ارتباط استریم را به دلیل خطای سرور یا تکمیل ظرفیت قطع کرد (503001).",
  "recommended_action_fa": "به اتصال مستقیم محلی RTSP یا ارتباط P2P بازگشت نمایید.",
  "recovery_strategy": "p2p_reconnect"
}
```
