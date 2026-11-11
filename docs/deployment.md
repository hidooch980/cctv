# Molido CCTV AI - Deployment & Operations Guide

## 1. Quick Start with Docker Compose

To launch the complete Molido CCTV AI platform (FastAPI Backend + Web Control Center + Nginx proxy):

```bash
docker compose up -d --build
```

Access the services:
- **Web Control Center**: `http://localhost`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/healthz`

Default administrator credentials:
- **Username**: `admin`
- **Password**: `Admin@123456`

## 2. Local Development Setup

### 2.1 Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run test suite:
```bash
pytest -v
```

### 2.2 Frontend
```bash
cd frontend
npm install
npm run dev
```

Build production bundle:
```bash
npm run build
```

## 3. Scaling to 100 Cameras Capacity
The platform baseline is configured for 100 cameras:
- **Database**: When exceeding 25 cameras, switch `DATABASE_URL` from SQLite to PostgreSQL (`postgresql+asyncpg://...`).
- **Network Bitrate**: 100 cameras @ 2.5 Mbps average require ~250 Mbps sustained network ingest throughput. Ensure host NIC is configured with 1 Gbps or 10 Gbps Ethernet with jumbo frames enabled if supported.
- **RTSP Connection Pooling**: Always prefer sub-stream (`subtype=1`) for the 4x4 (16-camera) and 3x3 matrix views to preserve CPU decoding and camera bandwidth. Switch to main stream on 1x1 full-screen view.
