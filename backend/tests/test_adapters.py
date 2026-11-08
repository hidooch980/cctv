import asyncio

import httpx

from app.adapters import _dahua_probe, _hikvision_probe, _onvif_discover


def test_onvif_profile_and_rtsp_uri_discovery_with_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        action = request.headers.get("Content-Type", "")
        if "GetCapabilities" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Capabilities><Media><XAddr>http://192.0.2.55/onvif/media_service</XAddr></Media></Capabilities></Body></Envelope>"""
        elif "GetProfiles" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Profiles token="profile_1"><Name>Camera 1</Name></Profiles><Profiles token="profile_2"><Name>Camera 2</Name></Profiles></Body></Envelope>"""
        elif "GetStreamUri" in action:
            body = """<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope"><Body><Uri>rtsp://operator:secret@192.0.2.55:554/Streaming/Channels/101</Uri></Body></Envelope>"""
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
    assert result.channels[0]["stream_uri"] == "rtsp://192.0.2.55:554/Streaming/Channels/101"
    assert "secret" not in result.channels[0]["stream_uri"]
    assert "rtsp_uri" in result.capabilities


def test_hikvision_isapi_channel_discovery():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/ISAPI/System/deviceInfo"):
            return httpx.Response(200, text="<DeviceInfo><manufacturer>Hikvision</manufacturer><model>DS-7608</model></DeviceInfo>")
        if request.url.path.endswith("/ISAPI/ContentMgmt/InputProxy/channels"):
            return httpx.Response(200, text="<InputProxyChannelList><InputProxyChannel><id>1</id><name>Front</name></InputProxyChannel><InputProxyChannel><id>2</id><name>Gate</name></InputProxyChannel></InputProxyChannelList>")
        return httpx.Response(404)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _hikvision_probe(client, "http://192.0.2.56", "admin", "secret")

    result = asyncio.run(run())
    assert result.adapter == "hikvision_isapi"
    assert result.model == "DS-7608"
    assert [c["name"] for c in result.channels] == ["Front", "Gate"]


def test_dahua_cgi_channel_discovery():
    def handler(request: httpx.Request) -> httpx.Response:
        if "magicBox.cgi" in request.url.path:
            return httpx.Response(200, text="deviceType=NVR5216")
        if "configManager.cgi" in request.url.path:
            return httpx.Response(200, text="table.ChannelTitle[0].Name=Entrance\ntable.ChannelTitle[1].Name=Parking\n")
        return httpx.Response(404)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _dahua_probe(client, "http://192.0.2.57", "admin", "secret")

    result = asyncio.run(run())
    assert result.adapter == "dahua_cgi"
    assert result.model == "NVR5216"
    assert [c["name"] for c in result.channels] == ["Entrance", "Parking"]
