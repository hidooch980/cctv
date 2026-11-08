# Molido CCTV AI — Android test client

The first Flutter Android shell is a **test UI**, branded with a Dahua-compatible visual direction. It is not an official Dahua application and does not imply Dahua endorsement.

## Included in 0.1.0
- Four-language dashboard: Persian (RTL), English (LTR), Arabic (RTL), and Turkish (LTR), switchable from Settings
- Localized navigation, dashboard metrics, camera management, events, alerts, and settings
- Camera inventory cards and add-camera flow
- API sync with the FastAPI inventory endpoints
- Editable central server URL
- Local demo camera cards when the backend is unavailable
- Test-mode messaging for features not wired to live devices

## Run
Install Flutter 3.24+ and Android SDK, then:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

Install on a connected Android phone:

```bash
flutter install
```

## Connect to backend
- Android emulator default: `http://10.0.2.2:8000`
- Physical phone: set the server URL to the reachable LAN/VPS address and port.
- Backend must expose `/api/v1/cameras`.
- For a physical device, use HTTPS in production. Cleartext HTTP is enabled only to support isolated local testing and must be disabled before release.

## Known limitations
- Camera tiles are placeholders; no RTSP video is rendered yet.
- ONVIF discovery, PTZ, playback, recording, push notifications and AI analytics are not implemented.
- Camera inventory in the current backend is in-memory and resets when the backend restarts.
- Demo cards are local-only and are not real camera connections.
