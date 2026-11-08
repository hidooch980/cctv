# Dahua DMSS P2P and DoLynk integration options

## Primary product target: DMSS-compatible P2P

DMSS is Dahua's official end-user mobile app. The Molido user experience should match its supported P2P add-device flow: scan the recorder QR or enter its serial number, then authenticate using the recorder's own username/password and any required device security step. The recorder must have P2P enabled and show Online while it has internet access; the phone may be on a different network.

This is a **workflow compatibility target**, not proof that Dahua exposes the same cloud transport/SDK to third-party applications. A supported, authorized third-party P2P SDK/API or partner interface is still required before Molido can establish cloud sessions or receive video. Never extract DMSS session tokens or reverse-engineer private cloud protocols.

## Separate enterprise option: DoLynk Developer

Dahua also describes DoLynk Developer as a cloud-based open platform for third-party integrations, with APIs for device management and cloud video functions. Do not assume this is the same service/API as consumer DMSS P2P, or that every DMSS device can be reached through DoLynk.

Published onboarding may require:
1. Register a developer account at the official DoLynk Developer portal.
2. Complete company authentication for full capabilities and production access.
3. Obtain the API documentation/SDK and credentials applicable to the target region/product.
4. Integrate with the documented APIs/SDK and Dahua technical support materials.

## Android and backend behavior

- Android offers a distinct **Dahua DMSS-compatible P2P** registration mode, separate from local IP and generic serial registration.
- Device serial/QR is an identifier only, never an authentication secret.
- The recorder must have P2P enabled and show Online on its own internet connection; the phone and recorder may be on different networks.
- P2P and PaaS/account mode may differ by client/account configuration, region, model and firmware. DMSS consumer P2P and DoLynk enterprise APIs must be assessed separately.
- Cloud account authorization, device online status, channel discovery, live video, playback and alarms are separate capabilities.
- Until official credentials and the approved adapter are configured, backend status explicitly reports `credentials_required`, `online=false`, `sdk_connected=false` and `cloud_video=false`. No successful connection is simulated.
- API credentials and device passwords must not be stored in source control, logs or inventory responses. Persistent secrets require reviewed encryption/key management.

## Molido API contract

- `POST /api/v1/recorders` with `connection_method=dahua_p2p` registers the Dahua serial identity.
- `GET /api/v1/recorders/{id}/p2p-status` reports integration readiness.
- `POST /api/v1/recorders/{id}/p2p-connect-test` returns a clear not-configured response until the official API adapter and credentials are supplied.
- The Dahua P2P mode is rejected for other brands.

## Required to enable live cloud connection

- Written confirmation from Dahua or an authorized partner of the third-party P2P SDK/API or partner interface that supports the target DMSS-compatible recorder flow.
- Official SDK/API documentation and licensing/terms for the deployment region.
- Any API application credentials and the documented device/account authorization flow, configured through a secure deployment secret manager.
- If DoLynk is selected instead, separate confirmation that the target devices and desired live-view/playback APIs are supported by that enterprise platform.
- Exact recorder model, firmware and region; then physical validation of online status, channels, live video, playback and reconnect behavior.

## Official references

- DoLynk Developer: https://www.dahuasecurity.com/products/software/dolynk-cloud/doylnk-product/eco
- Dahua SDK/software download center: https://www.dahuasecurity.com/download-center/softwares
- Dahua API portal: https://www.dahuasecurity.com/api/
- Dahua P2P/PaaS modes: https://dahuatech.zendesk.com/hc/en-gb/articles/39851775665554-Ports-of-P2P-PaaS-Services-Access-and-P2P-PaaS-Server-Domain-Name
