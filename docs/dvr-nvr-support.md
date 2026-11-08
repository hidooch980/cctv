# DVR and NVR support

Molido CCTV AI treats DVR, NVR and hybrid XVR appliances as first-class managed devices, alongside standalone IP cameras.

## Connection methods
The mobile user and recorder may be on completely different networks. For supported Dahua devices, the primary remote workflow is **Dahua DMSS-compatible P2P** using the recorder serial/QR and the recorder's own authentication. DMSS is the official Dahua mobile client; this workflow is the product target, not proof that its private cloud SDK/API is available to third parties. Local IP remains available, while Molido Gateway and secure Public IP/VPN are optional fallbacks. Availability depends on model, firmware, region and vendor authorization. See [remote connectivity architecture](remote-connectivity-architecture.md).

### A. Direct IP connection
- Connect directly over the reachable LAN/WAN IP address or hostname and configured service port.
- Inputs: IP/hostname, port, device username and device password.
- The recorder must be reachable from the Molido server/client and the account must have the required permissions.
- Port defaults are model/protocol-specific and must remain editable.

### B. Dahua DMSS-compatible P2P / cloud connection (primary remote workflow)
- Provide an optional serial-number entry path for manufacturers that support device binding or remote/P2P access by serial number.
- Match the DMSS add-device flow: scan QR or enter serial number, select the supported device type, then provide the recorder's device username/password and any model/app-version-specific security or pairing proof.
- The recorder's P2P feature must be enabled and report Online while the recorder itself has internet access. The phone can use a different internet connection/mobile data.
- The DMSS account password and recorder password are distinct; request only the recorder credentials needed by the authorized integration.
- Serial number alone is not assumed to authenticate or establish a connection. Do not bypass vendor authentication.
- Use only an authorized, documented Dahua P2P SDK/API/partner interface; never extract DMSS tokens or reverse-engineer private cloud traffic.
- Do not assume DoLynk Developer APIs are identical to consumer DMSS P2P. Treat DoLynk as a separate enterprise integration path requiring its own eligibility and documentation.
- Where no authorized third-party P2P interface is available, report the limitation and offer secure VPN/direct IP or the optional Molido gateway.
- QR scanning may be offered as a convenience to populate serial/device ID and pairing fields, but must not be mandatory.
- Do not require the user to create a vendor cloud account unless the specific manufacturer's documented connection method requires it.

### C. Molido outbound gateway (optional fallback)
- Install a Molido gateway/agent on a computer or appliance that can reach the DVR/NVR on its local network.
- The gateway establishes an outbound authenticated TLS session to Molido; no inbound port-forwarding is required on the recorder's router.
- The mobile app communicates with Molido, which authorizes a short-lived session through the paired gateway.
- The gateway performs the local Dahua CGI/ONVIF probe and returns sanitized channel/capability metadata.
- Live video requires a separately authorized media relay/tunnel; the control connection alone does not carry video.
- Gateway enrollment must be one-time, site-bound, revocable and protected by rotating credentials.

### D. Public IP / DNS direct remote connection
- Optional advanced path for an owner-managed, intentionally reachable recorder.
- Prefer VPN or restrictive firewall allowlists; do not expose recorder administration ports openly to the internet.
- Require TLS where supported and strong unique credentials. Validate destination and port to prevent SSRF and port scanning.

The UI must let the operator choose **Dahua DMSS-compatible P2P/Cloud** (primary remote workflow), **Local IP**, **Molido Gateway** or **Public IP/VPN** and show only fields required by the selected supported adapter.

## Device inventory
- Device type: DVR, NVR or XVR.
- Identity: friendly name, brand/model and site/location; serial number/device ID is optional and may be used by supported serial/P2P adapters.
- Connectivity: IP/hostname, port and a selected integration adapter (ONVIF, RTSP or vendor API/SDK).
- Health: device reachability, service/API health, storage health and last successful contact.
- Login: device username and password are supplied by the operator for direct device authentication.
- Security: never store passwords in plaintext or return them from inventory APIs. Persist credentials only in a dedicated encrypted secret store with key management; until that exists, accept them only transiently for a connection test/session. Never put credentials in URLs, logs, analytics or source control.

## Channel model
- Each recorder owns a channel inventory with stable recorder/channel identifiers.
- Channel metadata includes channel number, display name, enabled state, signal/connection state and linked camera identity when known.
- Channel states are distinct from recorder state: a reachable DVR can still have disconnected or failed channels.
- Recorder removal must not silently delete independent camera records; channel relationships should be detached or explicitly reconciled.

## Operator workflows
1. Choose IP connection or Serial/Device ID connection; enter the fields required by that recorder's supported adapter.
2. Discover supported channels and associate cameras.
3. Show live preview using the selected channel's supported RTSP/vendor stream path.
4. Search playback by recorder, channel, time range and event.
5. Surface recording schedule, retention, disk/RAID health and export capability only when exposed by the model's API.
6. Alert on recorder offline, channel loss, disk failure, recording gap and clock drift.

## Adapter coverage currently implemented
- **ONVIF (generic):** authenticated device capabilities, media service resolution, profile enumeration, and RTSP stream URI retrieval.
- **Hikvision:** ISAPI device information and supported input/stream channel endpoints; falls back to ONVIF when the ISAPI path is unavailable.
- **Dahua:** CGI system information and channel-title enumeration; ONVIF remains the fallback for media profiles and RTSP stream URIs.
- **Uniview, Tiandy and other ONVIF-capable brands:** generic ONVIF adapter path. A dedicated vendor API adapter is not yet certified for these brands.
- **Dahua DMSS-compatible P2P/Cloud:** serial/QR inventory is accepted, but live cloud authentication and video are not enabled until an authorized third-party P2P interface/SDK, account mode, authorization material and terms are available. DoLynk Developer is a separate possible enterprise route.
- **Molido Gateway / remote relay:** architecture is documented; gateway enrollment, outbound tunnel and media relay are not implemented yet.

The connection-test endpoint is \`POST /api/v1/recorders/{id}/connect-test\`; it accepts credentials for that single request, performs an authenticated probe, and does not persist the submitted username/password. Discovered channels are listed at \`GET /api/v1/recorders/{id}/channels\`.


ONVIF discovery/profile/media support, RTSP live streaming, and vendor-specific playback/export are separate adapter capabilities. They must be capability-detected and validated against actual model/firmware. A generic RTSP URL does not guarantee playback search or export support. Do not claim universal playback compatibility.

## Acceptance tests
- Exercise ONVIF profile enumeration and RTSP URI retrieval using mock SOAP responses; verify RTSP URIs never retain embedded credentials.
- Exercise Hikvision ISAPI and Dahua CGI channel parsers using mock HTTP responses.
- Register DVR/NVR/XVR through direct IP login and through serial/device-ID pairing where the vendor supports it.
- Verify serial-only input is not treated as authentication; require the vendor's documented proof/pairing flow.
- Verify credentials are never returned, logged or stored in plaintext; validate encrypted secret storage before persistent credential support is enabled.
- Generate and list a channel inventory and validate channel bounds.
- Keep recorder health separate from channel health.
- Verify channel-to-camera association and safe unlink behavior.
- Test live stream and recorded playback with authorized sample devices for each supported adapter.
- Verify storage/recording alerts against vendor-reported states.
- Load-test the intended number of recorders/channels and concurrent streams.

## Current implementation status
- Backend recorder inventory endpoints are implemented for create/list/read/delete at `/api/v1/recorders`.
- The backend accepts both direct IP login and serial/device-ID registration, and validates the required fields for each path.
- The Android app includes a four-language DVR/NVR/XVR registration form with a selectable IP or serial connection method.
- Submitted passwords and pairing codes are request-only fields; the recorder inventory database and API responses do not persist or expose them.
- Registration currently records device configuration with `pending` status. It does not yet establish a live vendor session.
- ONVIF, Hikvision ISAPI and Dahua CGI adapter code plus mock-transport tests are present. Mock tests do not prove compatibility with physical recorders.
- Physical-device connectivity, firmware-specific channel discovery, stream decoding, manufacturer P2P/SDK authentication, Molido gateway enrollment/tunnel, remote media relay, recorded playback and disk telemetry still require implementation and/or authorized hardware/firmware tests.
