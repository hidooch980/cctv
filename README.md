# Molido CCTV AI

Multi-brand video surveillance management platform (VMS).

## Product Baseline

- **Platforms**: Web Control Center, Android & iOS mobile applications, Windows desktop
- **Initial capacity target**: 100 cameras (subject to throughput and hardware validation)
- **Storage**: Hybrid local SSD caching + cloud/object storage for long-term retention
- **Integrations**: ONVIF discovery & control (Profile S/T/G), RTSP media ingest, Dahua / Lechange / Imou OpenSDK V3.8.0, Hikvision ISAPI, Uniview
- **AI Analytics**: Configurable video analytics (person, vehicle, virtual tripwire, tampering detection)
- **Languages**: Persian (فارسی - fa, RTL) and English (en, LTR) with instant switching

## Architecture

- `backend/`: FastAPI service, JWT authentication, camera inventory, PTZ dispatching, AI events, and OpenSDK error resolution engine
- `frontend/`: React + TypeScript + Vanilla CSS web control center with 1x1, 2x2, 3x3, 4x4 matrix view, live canvas video feed simulation, PTZ controller, event stream, and OpenSDK diagnostic modal
- `mobile/`: Android OpenSDK integration module (`OpenSDKManager.kt`, `OpenSDKErrorResolver.kt`, `BluetoothDoorManager.kt`)
- `deploy/`: Production Docker Compose definitions and Nginx reverse proxy configuration
- `docs/`: Comprehensive architecture, OpenSDK integration guide, REST API reference, and deployment procedures

## Quick Start

### 1. Docker Compose (Recommended)
```bash
docker compose up -d --build
```
- Web Control Center: `http://localhost`
- Backend API Docs (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

Default credentials: `admin` / `Admin@123456`

### 2. Local Development

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
npm run dev
```

## Testing & Quality Assurance
- **Backend**: Automated pytest test suite covering authentication, camera inventory, PTZ controls, system health, and OpenSDK error diagnosis (`pytest -v`).
- **Frontend**: Full TypeScript type safety and Vite production bundling (`npm run build`).

## Safety and Security
Only connect cameras and recorders that you own or are explicitly authorized to administer. Never expose camera RTSP credentials in client code or logs. Use TLS, least-privilege roles, audit logging, encrypted secrets, and network segmentation. Face recognition and other biometric features are disabled by default and require a documented lawful basis and explicit configuration.
