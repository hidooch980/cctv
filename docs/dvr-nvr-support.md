# DVR and NVR support

Molido CCTV AI treats DVR, NVR and hybrid XVR appliances as first-class managed devices, alongside standalone IP cameras.

## Device inventory
- Device type: DVR, NVR or XVR.
- Identity: brand, model, friendly name, site/location and firmware (when discovered).
- Connectivity: management host/port and a selected integration adapter (ONVIF, RTSP or vendor API/SDK).
- Health: device reachability, service/API health, storage health and last successful contact.
- Security: credentials must be stored in a dedicated encrypted secret store; never in camera/recorder inventory responses, logs, URLs or source control.

## Channel model
- Each recorder owns a channel inventory with stable recorder/channel identifiers.
- Channel metadata includes channel number, display name, enabled state, signal/connection state and linked camera identity when known.
- Channel states are distinct from recorder state: a reachable DVR can still have disconnected or failed channels.
- Recorder removal must not silently delete independent camera records; channel relationships should be detached or explicitly reconciled.

## Operator workflows
1. Add a recorder by brand/model, host, port, recorder type and channel count.
2. Discover supported channels and associate cameras.
3. Show live preview using the selected channel's supported RTSP/vendor stream path.
4. Search playback by recorder, channel, time range and event.
5. Surface recording schedule, retention, disk/RAID health and export capability only when exposed by the model's API.
6. Alert on recorder offline, channel loss, disk failure, recording gap and clock drift.

## Integration boundaries
ONVIF discovery/profile/media support, RTSP live streaming, and vendor-specific playback/export are separate adapter capabilities. They must be capability-detected and validated against actual model/firmware. A generic RTSP URL does not guarantee playback search or export support. Do not claim universal playback compatibility.

## Acceptance tests
- Register DVR/NVR/XVR metadata without persisting submitted credentials.
- Generate and list a channel inventory and validate channel bounds.
- Keep recorder health separate from channel health.
- Verify channel-to-camera association and safe unlink behavior.
- Test live stream and recorded playback with authorized sample devices for each supported adapter.
- Verify storage/recording alerts against vendor-reported states.
- Load-test the intended number of recorders/channels and concurrent streams.

## Current implementation status
This document records the product and integration contract. It does not claim that physical DVR/NVR connectivity, live streaming, recorded playback, disk telemetry, or vendor-specific discovery has been implemented or tested. Those require adapter code and authorized hardware/firmware test fixtures.
