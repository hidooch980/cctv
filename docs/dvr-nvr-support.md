# DVR and NVR support

Molido CCTV AI treats DVR, NVR and hybrid XVR appliances as first-class managed devices, alongside standalone IP cameras.

## Connection methods (both supported in the product design)
Molido must offer two selectable connection paths. The available path depends on the recorder brand, model, firmware and vendor-supported interfaces.

### A. Direct IP connection
- Connect directly over the reachable LAN/WAN IP address or hostname and configured service port.
- Inputs: IP/hostname, port, device username and device password.
- The recorder must be reachable from the Molido server/client and the account must have the required permissions.
- Port defaults are model/protocol-specific and must remain editable.

### B. Serial-number / device-ID connection
- Provide an optional serial-number entry path for manufacturers that support device binding or remote/P2P access by serial number.
- Inputs may include serial number/device ID plus the vendor-required verification code, device password, account authorization or other pairing proof.
- Serial number alone is not assumed to authenticate or establish a connection. Do not bypass vendor authentication.
- Where supported, use the manufacturer's documented SDK/API/P2P service. Where unsupported, clearly explain that this model requires direct IP connection.
- QR scanning may be offered as a convenience to populate serial/device ID and pairing fields, but must not be mandatory.
- Do not require the user to create a vendor cloud account unless the specific manufacturer's documented connection method requires it.

The UI must let the operator choose **IP connection** or **Serial/Device ID connection** and show only the fields required by the selected supported adapter.

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

## Integration boundaries
ONVIF discovery/profile/media support, RTSP live streaming, and vendor-specific playback/export are separate adapter capabilities. They must be capability-detected and validated against actual model/firmware. A generic RTSP URL does not guarantee playback search or export support. Do not claim universal playback compatibility.

## Acceptance tests
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
This document records the product and integration contract. The product design supports both direct IP + port + device login and optional serial/device-ID pairing through documented vendor-supported methods. It does not claim that physical DVR/NVR connectivity, live streaming, recorded playback, disk telemetry, or vendor-specific discovery has been implemented or tested. Those require adapter code and authorized hardware/firmware test fixtures.
