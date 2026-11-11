# Molido CCTV AI - REST API Reference

The Molido CCTV AI backend provides an OpenAPI 3.0 compatible RESTful API under the prefix `/api/v1`.

Interactive Swagger documentation is available locally at:
`http://localhost:8000/docs`

## 1. Authentication (`/api/v1/auth`)

- `POST /api/v1/auth/login`: Authenticate with username and password, returns JWT token.
- `POST /api/v1/auth/token`: OAuth2 password form login.
- `GET /api/v1/auth/me`: Returns profile of authenticated user.
- `POST /api/v1/auth/users`: Register new operator user (Admin only).

## 2. Camera Management (`/api/v1/cameras`)

- `GET /api/v1/cameras`: Query camera list (filter by group or status).
- `POST /api/v1/cameras`: Register camera in inventory (capacity checked against 100 max limit).
- `GET /api/v1/cameras/{id}`: Fetch single camera details.
- `PUT /api/v1/cameras/{id}`: Update camera stream/network configurations.
- `DELETE /api/v1/cameras/{id}`: Remove camera from system.
- `GET /api/v1/cameras/{id}/stream`: Fetch WebRTC, HLS, and sanitized RTSP endpoints.
- `POST /api/v1/cameras/{id}/ptz`: Dispatch mechanical PTZ commands (`pan_left`, `pan_right`, `tilt_up`, `tilt_down`, `zoom_in`, `zoom_out`, `stop`).
- `POST /api/v1/cameras/discover`: Scan LAN network for ONVIF and OpenSDK compatible cameras.

## 3. Events & AI Analytics (`/api/v1/events`)

- `GET /api/v1/events`: Fetch security detection events (filter by camera ID or event type).
- `POST /api/v1/events`: Ingest new AI event from edge inference engine.
- `POST /api/v1/events/{id}/acknowledge`: Mark alert as reviewed by security operator.

## 4. System Health & Capacity (`/api/v1/system`)

- `GET /api/v1/system/health`: System uptime, active cameras vs capacity target, disk usage, aggregate stream bitrate.

## 5. OpenSDK Diagnostics & Error Resolver (`/api/v1/opensdk`)

- `GET /api/v1/opensdk/catalog`: Full registry of Dahua/Imou OpenSDK and RTSP error codes.
- `POST /api/v1/opensdk/diagnose`: Diagnose status code with bilingual English & Persian root cause analysis and remediation strategy.
