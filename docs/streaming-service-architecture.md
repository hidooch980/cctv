# Molido CCTV streaming service architecture

## Design decision

Separate the **control plane** (device inventory, authorization, session issuance and audit) from the **media plane** (RTSP ingest, remux/transcode, HLS/WebRTC delivery). FastAPI remains the control plane. A dedicated media gateway is responsible for video transport; camera RTSP must never be exposed directly to the Android client.

## Target topology

```text
Android app
   | HTTPS: login, device/channel list, start/stop session
   v
FastAPI control plane ---- tenant/user/device authorization + audit
   | short-lived signed provider command
   v
Media gateway (MediaMTX-class service)
   | RTSP over TCP from site gateway / LAN connector
   v
DVR / NVR / IP camera

Android player <---- short-lived HLS or WebRTC playback URL ---- Media gateway
```

For remote sites behind NAT, a site connector initiates an outbound mutually authenticated TLS tunnel. Do not require public inbound camera ports or expose recorder administration interfaces to the internet.

## Playback modes

- **WebRTC:** preferred for interactive low-latency live view where the gateway/network supports it.
- **HLS:** compatibility/fallback mode for mobile playback and constrained networks; latency depends on segment settings.
- **RTSP:** ingest-only between trusted gateway and recorder. Never return raw RTSP URLs, usernames or passwords to mobile clients.
- **Playback/archive:** a separate capability and API from live view. It must be enabled only when the device or authorized cloud provider exposes a supported recording-search/download interface.

## Session lifecycle

1. Client requests a session for an authorized recorder channel and a named profile (main/sub).
2. Control plane checks tenant/site/device/channel permissions and device connectivity.
3. Provider receives a scoped command with an expiry; it creates an isolated path and returns a short-lived playback URL.
4. Client consumes HLS/WebRTC URL. The URL is bound to the session/user/device, expires quickly and can be revoked.
5. Client stop, expiry, permission revocation or gateway disconnect closes the media session.
6. Audit records store identifiers, timestamps, transport and outcome only—never secrets or full signed URLs.

## Security and reliability requirements

- Enforce tenant isolation and authorization on every start, read and stop request.
- Use TLS end-to-end for control and media signaling; use signed, short-lived playback tokens.
- Keep device credentials in a secret manager or encrypted credential vault; never place them in RTSP URLs persisted in the database, app logs or API responses.
- Avoid command-line argument exposure of RTSP credentials. A production provider must use a protected secret/config channel.
- Allowlist site connector destinations and recorder addresses; defend against SSRF, DNS rebinding and arbitrary port scanning.
- Per-user and per-site concurrent stream quotas; bounded bitrate/resolution; idle timeout; reconnect with backoff.
- Health metrics: ingest state, first-frame time, bitrate, packet loss, reconnect count, provider errors and active sessions.
- Keep audio, PTZ, snapshots, live video and recorded playback as separately permissioned capabilities.
- Use a process supervisor/container health checks and restart policy for the media gateway; do not run unbounded FFmpeg child processes inside API workers.

## Provider contract added to the codebase

`backend/app/streaming.py` defines provider-neutral HLS/WebRTC session commands and a safe disabled provider. Until a production media gateway is configured, the API must return an explicit unavailable/not-configured result and must not report a successful stream.

## Staged implementation

1. **Control-plane contract (current foundation):** transport/profile enums, provider interface, explicit disabled state, API capability and session-request validation.
2. **Media gateway deployment:** choose and pin a supported MediaMTX release; deploy behind TLS; configure authenticated API, storage, metrics and resource limits.
3. **Site connector:** outbound mTLS tunnel, site/device allowlists, credential vault and revocation.
4. **Live ingest:** RTSP-over-TCP from local connector to gateway; WebRTC first, HLS fallback; no raw RTSP on mobile.
5. **Archive playback:** separate vendor-specific adapter; test time search, playback, seek and export.
6. **Hardware acceptance:** real Dahua NVR/camera, firmware, stream profiles, LAN and remote-network tests; record measured latency and reconnect behavior.

## Dahua cloud integration boundary

DoLynk Developer is an official third-party cloud platform with standardized APIs/SDKs for device access, cloud live video/playback and messages. It is not the same thing as the DMSS consumer P2P transport. The Dahua adapter must be implemented only after Dahua confirms the product/model/region eligibility and provides the relevant SDK/API docs, license and application credentials. Keep the provider behind the same `StreamProvider` contract so a future official Dahua provider does not couple the app to undocumented DMSS internals.

## Required acceptance evidence

- A real device and exact model/firmware/region.
- Authorized Dahua developer/partner access and official docs/SDK/API, if cloud P2P is required.
- Successful live-view and playback evidence from a phone on a different network.
- Session expiry/revocation, credential non-disclosure, tenant-isolation and reconnect tests.
- Measured first-frame latency, sustained bitrate and reconnect results. Unit tests or simulated providers are not hardware acceptance.
