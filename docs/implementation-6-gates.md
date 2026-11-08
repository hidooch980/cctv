# Six-gate implementation status

Branch: `feat/molido-cctv-ai-foundation`

## Gate 1 — Android build and device validation
- Debug APK build is produced by GitHub Actions.
- Flutter static analysis and widget smoke tests run in CI.
- Physical-device installation, Android-version compatibility, camera LAN reachability, and long-session behavior require a real handset and the target network; CI cannot certify these.

## Gate 2 — Mobile/backend integration
- The Flutter client can add cameras and synchronize the inventory through the FastAPI endpoints.
- The default Android emulator URL is `http://10.0.2.2:8000`; a physical phone must be configured with a reachable server address.
- Production authentication, authorization, TLS trust validation, and secret handling remain required before exposing the API beyond a trusted test network.

## Gate 3 — Durable inventory
- Camera inventory is persisted in SQLite at `MOLIDO_CCTV_DATABASE_PATH` (default `data/cameras.db`).
- CRUD, persistence across app-state reset, credential non-disclosure, URL rejection, and the 100-record limit have automated tests.
- Credentials are deliberately not accepted as stored secrets until an encrypted secret vault and key-management policy are implemented.

## Gate 4 — ONVIF and RTSP
- Camera metadata supports `onvif`, `rtsp`, and `vendor_api` protocol labels.
- Actual ONVIF discovery, authenticated device information/profile retrieval, RTSP session negotiation, decoding, and live playback are not yet implemented or certified.
- These require camera models/firmware, reachable LAN devices, authorized test credentials, and a streaming runtime (for example FFmpeg/GStreamer). Do not treat protocol labels as proof of live support.

## Gate 5 — 100-camera / multi-view validation
- The API enforces a maximum of 100 registered camera records and has a 100-record regression test.
- Multi-view UI tiles are placeholders, not live streams.
- Sustained 100-stream throughput, latency, storage, CPU/GPU, bitrate, and reconnect tests require actual camera feeds and representative hardware. The registration cap is not a 100-live-stream performance guarantee.

## Gate 6 — Signed Android release
- A manual GitHub Actions release workflow and Gradle signing configurator are committed.
- Configure repository Actions secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `ANDROID_STORE_PASSWORD`.
- The workflow intentionally skips release generation when secrets are absent. Debug APKs are not production releases.
- The keystore must be generated and backed up by the project owner; it must never be committed to Git.

## CI
- Backend checks run with pytest.
- Android checks run Flutter analyze, widget tests, and debug APK build.
