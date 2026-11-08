import asyncio

import httpx

from app.adapters import _onvif_discover


def test_onvif_profile_and_rtsp_uri_discovery_with_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        action = request.headers.get("Content-Type", "")
        if "GetCapabilities" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Capabilities><Media><XAddr>http://192.0.2.55/onvif/media_service</XAddr></Media></Capabilities></Body></Envelope>"""
        elif "GetProfiles" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Profiles token="profile_1"><Name>Camera 1</Name></Profiles><Profiles token="profile_2"><Name>Camera 2</Name></Profiles></Body></Envelope>"""
        elif "GetStreamUri" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Uri>rtsp://192.0.2.55:554/Streaming/Channels/101</Uri></Body></Envelope>"""
        else:
            return httpx.Response(500)
        return httpx.Response(200, text=body)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _onvif_discover(client, "http://192.0.2.55", "operator", "secret")

    result = asyncio.run(run())
    assert result.reachable is True
    assert result.adapter == "onvif"
    assert len(result.channels) == 2
    assert result.channels[0]["name"] == "Camera 1"
    assert result.channels[0]["stream_uri"].startswith("rtsp://")
    assert "rtsp_uri" in result.capabilities
