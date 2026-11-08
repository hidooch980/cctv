"""Provider-neutral stream control plane.

The application never returns raw RTSP URLs or camera credentials to mobile clients.
A production provider must return an authenticated, short-lived HLS/WebRTC playback URL.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID


class StreamTransport(str, Enum):
    hls = "hls"
    webrtc = "webrtc"


class StreamProfile(str, Enum):
    main = "main"
    sub = "sub"


@dataclass(frozen=True)
class StreamStartCommand:
    tenant_id: str
    user_id: str
    recorder_id: UUID
    channel_id: UUID
    transport: StreamTransport
    profile: StreamProfile
    expires_at: datetime


@dataclass(frozen=True)
class StreamSession:
    session_id: UUID
    playback_url: str
    transport: StreamTransport
    expires_at: datetime


class StreamProvider(Protocol):
    """Media-plane contract implemented by MediaMTX or an approved vendor SDK."""

    name: str

    async def start(self, command: StreamStartCommand) -> StreamSession: ...

    async def stop(self, session_id: UUID) -> None: ...


class ProviderNotConfigured(RuntimeError):
    pass


class DisabledStreamProvider:
    """Safe default: never pretends a camera is streaming."""

    name = "disabled"

    async def start(self, command: StreamStartCommand) -> StreamSession:
        raise ProviderNotConfigured(
            "No production media provider is configured. Configure and validate "
            "the media gateway before issuing playback sessions."
        )

    async def stop(self, session_id: UUID) -> None:
        raise ProviderNotConfigured("No production media provider is configured.")
