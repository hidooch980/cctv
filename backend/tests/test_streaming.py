from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.streaming import (
    DisabledStreamProvider,
    ProviderNotConfigured,
    StreamProfile,
    StreamStartCommand,
    StreamTransport,
)


@pytest.mark.asyncio
async def test_disabled_provider_never_fakes_a_stream():
    provider = DisabledStreamProvider()
    command = StreamStartCommand(
        tenant_id="test-tenant",
        user_id="test-user",
        recorder_id=uuid4(),
        channel_id=uuid4(),
        transport=StreamTransport.hls,
        profile=StreamProfile.sub,
        expires_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ProviderNotConfigured):
        await provider.start(command)


@pytest.mark.asyncio
async def test_disabled_provider_does_not_claim_stop_success():
    provider = DisabledStreamProvider()
    with pytest.raises(ProviderNotConfigured):
        await provider.stop(uuid4())
