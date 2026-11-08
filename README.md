# Molido CCTV AI

Multi-brand video surveillance management platform.

## Product baseline

- Platforms: Web, Windows desktop, Android and iOS
- Initial capacity target: 100 cameras (subject to throughput and hardware validation)
- Storage: hybrid local + cloud/object storage
- Integrations: ONVIF discovery/control where supported, RTSP media ingest, vendor APIs
- AI: configurable video analytics (person, vehicle, events, optional license-plate processing)
- Languages: Persian (fa) and English (en)

## Architecture

- `backend/`: FastAPI service, authentication, camera inventory, events and APIs
- `frontend/`: web control center
- `desktop/`: Windows desktop packaging
- `mobile/`: cross-platform mobile application
- `deploy/`: deployment examples and operations
- `docs/`: architecture, security, compatibility and operations

## Safety and security

Only connect cameras and recorders that you own or are explicitly authorized to administer. Never expose camera RTSP credentials in client code or logs. Use TLS, least-privilege roles, audit logging, encrypted secrets, and network segmentation. Face recognition and other biometric features are disabled by default and require a documented lawful basis and explicit configuration.

## Development status

Repository bootstrap. No live camera connectivity, recording, AI inference, or production deployment is claimed until implemented and tested against real devices.
