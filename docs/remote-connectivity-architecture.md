# Remote connectivity architecture

## Goal

A Molido mobile user and a Dahua (or other supported) DVR/NVR may be on completely different networks. Local-LAN discovery and private RFC1918 IP addresses are not a remote-access strategy. Remote access must be an explicit connection mode with a documented, authenticated path.

## Supported connection modes

1. **Vendor P2P / cloud** — preferred when the exact model and firmware support an official vendor SDK/API and the required authorization is available. The serial/device ID is a locator, not a password. Pairing must use the vendor's documented proof/approval flow.
2. **Molido outbound gateway (recommended product direction)** — a small on-premises gateway/agent, installed on the recorder's LAN, makes an outbound TLS connection to the Molido service. The mobile app connects to Molido; the gateway opens an authorized, short-lived tunnel to the selected recorder. No inbound router port-forwarding is required. The gateway must be paired to a tenant/site and use rotating, revocable credentials.
3. **Public IP / DNS direct remote access** — optional advanced mode only when the owner has intentionally configured secure reachability. Require TLS where supported, strong device credentials, firewall allowlists/VPN where possible, and warn against exposing recorder admin ports directly to the public internet.
4. **Local IP** — retained for same-LAN installations and local discovery.

## Proposed request flow for the Molido gateway

1. An administrator creates a site and one-time gateway enrollment token in Molido.
2. The gateway is installed on a machine that can reach the DVR/NVR locally.
3. The gateway initiates an outbound TLS/WebSocket or mutually authenticated HTTPS session to Molido. It never accepts unsolicited public inbound connections.
4. The backend binds the gateway identity to the tenant/site and records heartbeat, software version and capabilities.
5. The operator adds a recorder by local address/port and supplies its credentials through a protected pairing flow.
6. The gateway performs the model-specific probe locally and returns only sanitized device metadata, channel inventory and capability results.
7. Live video uses a separate authenticated media relay/tunnel with per-session authorization, expiry and bandwidth limits. Control/API traffic must not be treated as a video transport.
8. Disconnecting/revoking a gateway immediately invalidates its sessions and tokens.

## Security requirements

- Tenant isolation and explicit site/gateway/device authorization on every operation.
- Short-lived, scoped access tokens; one-time enrollment tokens; rotation and revocation.
- Mutual TLS or equivalent strong gateway authentication.
- TLS for app-to-cloud, gateway-to-cloud and media relay legs.
- No plaintext device credentials in logs, analytics, URLs, crash reports or inventory APIs.
- Device credentials must be encrypted at rest with managed keys before persistent storage is enabled. Until then, credentials are transient and session-scoped.
- Validate all gateway-reported destinations and device addresses. Prevent SSRF, arbitrary port scanning and cross-tenant routing.
- Rate limits, audit events, session expiry, replay protection and abuse monitoring.
- Do not expose raw RTSP credentials or unrestricted RTSP URLs to the mobile client. Use a short-lived authorized media session.
- Do not claim end-to-end encrypted video unless every relay and key-management stage actually provides it.

## Dahua P2P / serial-number path

- Implement only against a documented, authorized Dahua SDK/API and its licensing/terms.
- Determine exact model, firmware, region and P2P/cloud availability before enabling the adapter.
- Serial number alone never authenticates a device.
- If the official SDK/API is unavailable, show the device as “P2P not configured” and offer Molido Gateway or secure public/VPN reachability where suitable.
- Do not reverse-engineer private cloud protocols or bypass vendor authentication.

## Implementation stages

- **Stage 1 — design and UX:** distinguish Local IP, Vendor P2P/Serial, Molido Gateway and Public IP modes; explain which require same LAN, gateway installation or vendor authorization.
- **Stage 2 — gateway enrollment/control plane:** site binding, one-time enrollment, authenticated heartbeat, gateway inventory, revoke/rotate, audit log.
- **Stage 3 — local device connector:** gateway-side Dahua CGI/ONVIF probes and channel discovery, with strict destination allowlists and credential handling.
- **Stage 4 — media relay:** short-lived stream sessions, per-user permissions, transcoding only if needed, quotas and observability.
- **Stage 5 — hardware validation:** test each exact recorder model/firmware and network topology. Simulated tests are not physical-device certification.

## Current status (truthful)

The existing backend has local/direct-IP adapter probes for Dahua CGI, Hikvision ISAPI and generic ONVIF, plus simulated tests. The serial/device-ID path currently stores inventory identity only; it does not establish a vendor P2P session. No Molido gateway enrollment service, outbound tunnel, cloud relay or remote video relay is implemented yet. A physical recorder and a gateway on its LAN are required to validate the complete remote path.
