# Dahua DoLynk Developer integration

## Selected route

Molido's Dahua remote-cloud adapter targets Dahua's official **DoLynk Developer** platform/API. Dahua describes this as a cloud-based open platform for third-party integrations, with standardized APIs, cloud live streaming/playback, cloud messages and secure device management.

Published Dahua onboarding:
1. Register a developer account at the official DoLynk Developer portal.
2. Complete company authentication for full capabilities and production access.
3. Generate API credentials/tokens.
4. Integrate with the documented APIs/SDK and Dahua technical support materials.

## Android and backend behavior

- Android offers a distinct **Dahua official P2P Cloud** mode, separate from local IP and generic serial registration.
- Device serial/QR is an identifier only, never an authentication secret.
- The recorder must have P2P enabled and show Online on its own internet connection.
- P2P and PaaS/account mode may differ by client/account configuration, region, model and firmware.
- Cloud account authorization, device online status, channel discovery, live video, playback and alarms are separate capabilities.
- Until official credentials and the approved adapter are configured, backend status explicitly reports `credentials_required`, `online=false`, `sdk_connected=false` and `cloud_video=false`. No successful connection is simulated.
- API credentials and device passwords must not be stored in source control, logs or inventory responses. Persistent secrets require reviewed encryption/key management.

## Molido API contract

- `POST /api/v1/recorders` with `connection_method=dahua_p2p` registers the Dahua serial identity.
- `GET /api/v1/recorders/{id}/p2p-status` reports integration readiness.
- `POST /api/v1/recorders/{id}/p2p-connect-test` returns a clear not-configured response until the official API adapter and credentials are supplied.
- The Dahua P2P mode is rejected for other brands.

## Required to enable live cloud connection

- Dahua developer account and completed company verification.
- Official API documentation/SDK package and licensing/terms for the deployment region.
- API application credentials and the documented device/account authorization flow, configured through a secure deployment secret manager.
- Exact recorder model, firmware and region; then physical validation of online status, channels, live video, playback and reconnect behavior.

## Official references

- DoLynk Developer: https://www.dahuasecurity.com/products/software/dolynk-cloud/doylnk-product/eco
- Dahua SDK/software download center: https://www.dahuasecurity.com/download-center/softwares
- Dahua API portal: https://www.dahuasecurity.com/api/
- Dahua P2P/PaaS modes: https://dahuatech.zendesk.com/hc/en-gb/articles/39851775665554-Ports-of-P2P-PaaS-Services-Access-and-P2P-PaaS-Server-Domain-Name
