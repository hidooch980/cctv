# DVR and NVR support

Molido CCTV AI treats DVR, NVR and hybrid XVR appliances as first-class managed devices, alongside standalone IP cameras.

## Connection method (IP + device login only)
- The operator connects directly to the DVR/NVR over its reachable LAN/WAN IP address and configured service port.
- Required connection inputs: IP address or hostname, port, device username and device password.
- Device type (DVR/NVR/XVR), brand and model may be selected to choose the correct protocol adapter.
- Serial number, QR code, P2P/cloud device ID, vendor cloud account and serial-based binding are not required and are not part of the connection flow.
- The device must be reachable from the Molido server/mobile client over the network, and the entered account must have the required device permissions.
- Port values are model/protocol-specific; the UI may suggest common defaults but must allow the operator to enter the actual configured port.

## Device inventory
- Device type: DVR, NVR or XVR.
- Identity: friendly name, brand/model and site/location; serial number is not required or used for connection.
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
1. Add a recorder using IP/hostname, port, device username and password; choose DVR/NVR/XVR and optionally brand/model. No serial number or cloud ID is requested.
2. Discover supported channels and associate cameras.
3. Show live preview using the selected channel's supported RTSP/vendor stream path.
4. Search playback by recorder, channel, time range and event.
5. Surface recording schedule, retention, disk/RAID health and export capability only when exposed by the model's API.
6. Alert on recorder offline, channel loss, disk failure, recording gap and clock drift.

## Integration boundaries
ONVIF discovery/profile/media support, RTSP live streaming, and vendor-specific playback/export are separate adapter capabilities. They must be capability-detected and validated against actual model/firmware. A generic RTSP URL does not guarantee playback search or export support. Do not claim universal playback compatibility.

## Acceptance tests
- Register DVR/NVR/XVR using IP/port and device login; confirm serial number is not required or used.
- Verify credentials are never returned, logged or stored in plaintext; validate encrypted secret storage before persistent credential support is enabled.
- Generate and list a channel inventory and validate channel bounds.
- Keep recorder health separate from channel health.
- Verify channel-to-camera association and safe unlink behavior.
- Test live stream and recorded playback with authorized sample devices for each supported adapter.
- Verify storage/recording alerts against vendor-reported states.
- Load-test the intended number of recorders/channels and concurrent streams.

## Current implementation status
This document records the product and integration contract. The selected connection design is direct IP + port + device username/password, not serial/cloud/P2P binding. It does not claim that physical DVR/NVR connectivity, live streaming, recorded playback, disk telemetry, or vendor-specific discovery has been implemented or tested. Those require adapter code and authorized hardware/firmware test fixtures.
