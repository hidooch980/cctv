# Molido CCTV AI - Platform Architecture

## 1. Overview
Molido CCTV AI is a high-performance, multi-brand video surveillance management platform (VMS) engineered to support up to 100 cameras on initial baseline deployments across Web, Windows desktop, Android, and iOS clients.

```mermaid
graph TD
    subgraph Edge Cameras & Devices
        C1["ONVIF Profile S/T Cameras"]
        C2["Dahua / Imou (OpenSDK / P2P)"]
        C3["Hikvision ISAPI / RTSP"]
        C4["Uniview & Generic RTSP"]
    end

    subgraph Molido Media Ingest & Backend
        ING["Media Ingest & RTSP Proxy Engine"]
        DISC["Network Discovery (WS-Discovery / OpenSDK)"]
        FAST["FastAPI Control Plane (Port 8000)"]
        DB[("SQLite / PostgreSQL Database")]
        DIAG["OpenSDK Error Diagnostics Engine"]
    end

    subgraph AI Video Analytics
        AI_DET["YOLO / Person & Vehicle Detector"]
        AI_LINE["Virtual Tripwire & Tampering Detection"]
    end

    subgraph Client Applications
        WEB["Web Control Center (React + TS + Nginx)"]
        MOB["Android & iOS Apps (OpenSDK Bridge)"]
        DSK["Windows Desktop App"]
    end

    C1 -->|RTSP / ONVIF| ING
    C2 -->|OpenSDK P2P / RTSP| ING
    C3 -->|RTSP| ING
    C4 -->|RTSP| ING
    DISC --> FAST
    ING --> FAST
    FAST --> DB
    FAST --> DIAG
    ING --> AI_DET
    AI_DET --> AI_LINE
    AI_LINE -->|Security Events| FAST
    FAST -->|REST / WebSocket / WebRTC| WEB
    FAST -->|REST / OpenSDK Native| MOB
    FAST -->|REST / Native Media| DSK
```

## 2. Platform Core Components

### 2.1 Backend (`backend/`)
- **FastAPI Core**: Async REST API handling authentication (JWT), camera inventory, operational metrics, PTZ telemetry, and security events.
- **Async Database Layer**: SQLAlchemy 2.0 with async SQLite (`aiosqlite`) default, fully ready for PostgreSQL (`asyncpg`).
- **OpenSDK Error Resolution Engine**: Diagnostic catalog mapping vendor codes (e.g. RTSP 401, 503, DHHTTP 503001, DEC_KEY_ERROR) to root cause analysis and automated remediation strategies.

### 2.2 Web Control Center (`frontend/`)
- Built with React 19, TypeScript, and high-performance Vanilla CSS.
- Multi-matrix view (1x1, 2x2, 3x3, 4x4) with real-time video simulation and overlay telemetry.
- Bilingual support: English (en, LTR) and Persian (fa, RTL) with instant language switching.
- PTZ mechanical joystick controller and integrated OpenSDK error resolver.

### 2.3 Mobile & OpenSDK Ingest (`mobile/`)
- Native Kotlin / Swift bindings for Dahua/Imou OpenSDK V3.8.0.
- P2P hole-punching session configuration (`OpenSDK_LoginManager`).
- Bluetooth Low Energy (BLE) smart door access module.

### 2.4 Hybrid Storage Model
- Local SSD cache for low-latency playback buffering and real-time motion snapshots.
- Object storage (S3 / MinIO compatible) for long-term historical recordings with retention policies.
