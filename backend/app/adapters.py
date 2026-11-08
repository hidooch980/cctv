from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx


SOAP_ENV = "http://www.w3.org/2003/05/soap-envelope"
DEVICE_NS = "http://www.onvif.org/ver10/device/wsdl"
MEDIA_NS = "http://www.onvif.org/ver10/media/wsdl"


@dataclass
class AdapterResult:
    reachable: bool
    adapter: str
    manufacturer: str | None
    model: str | None
    channels: list[dict[str, Any]]
    capabilities: list[str]
    warnings: list[str]


def _envelope(body: str) -> str:
    return (
        f'<s:Envelope xmlns:s="{SOAP_ENV}" xmlns:tds="{DEVICE_NS}" '
        f'xmlns:trt="{MEDIA_NS}"><s:Header/><s:Body>{body}</s:Body></s:Envelope>'
    )


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(root: ET.Element, name: str) -> str | None:
    for node in root.iter():
        if _local(node.tag) == name and node.text:
            return node.text.strip()
    return None


def _safe_stream_uri(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "rtsp" or not parsed.hostname:
        return None
    # Never persist usernames/passwords returned inside an ONVIF RTSP URI.
    host = parsed.hostname
    if parsed.port:
        host += f":{parsed.port}"
    return urlunsplit(("rtsp", host, parsed.path, parsed.query, ""))


def _base_urls(host: str, port: int | None) -> list[str]:
    candidates = []
    if port:
        scheme = "https" if port == 443 else "http"
        candidates.append(f"{scheme}://{host}:{port}")
    candidates.extend([f"http://{host}", f"https://{host}"])
    return list(dict.fromkeys(candidates))


async def _soap(
    client: httpx.AsyncClient,
    endpoint: str,
    username: str,
    password: str,
    action: str,
    body: str,
) -> ET.Element:
    response = await client.post(
        endpoint,
        content=_envelope(body),
        headers={
            "Content-Type": f'application/soap+xml; charset=utf-8; action="{action}"',
            "SOAPAction": f'"{action}"',
        },
        auth=httpx.DigestAuth(username, password),
    )
    response.raise_for_status()
    return ET.fromstring(response.content)


async def _onvif_discover(
    client: httpx.AsyncClient, base: str, username: str, password: str
) -> AdapterResult:
    device_service = base.rstrip("/") + "/onvif/device_service"
    capabilities = await _soap(
        client, device_service, username, password,
        DEVICE_NS + "/GetCapabilities",
        '<tds:GetCapabilities><tds:Category>Media</tds:Category></tds:GetCapabilities>',
    )
    media_xaddr = None
    for node in capabilities.iter():
        if _local(node.tag) == "Media":
            media_xaddr = _text(node, "XAddr")
            if media_xaddr:
                break
    media_url = media_xaddr or base.rstrip("/") + "/onvif/media_service"
    parsed = urlsplit(media_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Recorder returned an invalid ONVIF media endpoint")
    if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        # Use the device-provided media service only when it points to the same host.
        if parsed.hostname != urlsplit(base).hostname:
            raise ValueError("Recorder returned a cross-host ONVIF media endpoint")

    profiles_xml = await _soap(
        client, media_url, username, password,
        MEDIA_NS + "/GetProfiles", "<trt:GetProfiles/>",
    )
    profile_nodes = [node for node in profiles_xml.iter() if _local(node.tag) == "Profiles"]
    channels: list[dict[str, Any]] = []
    for index, profile in enumerate(profile_nodes[:128], start=1):
        token = profile.attrib.get("token")
        name = _text(profile, "Name") or f"Channel {index}"
        if not token:
            continue
        stream_uri = None
        try:
            uri_xml = await _soap(
                client, media_url, username, password,
                MEDIA_NS + "/GetStreamUri",
                '<trt:GetStreamUri><trt:StreamSetup><trt:Stream>RTP-Unicast</trt:Stream>'
                '<trt:Transport><trt:Protocol>RTSP</trt:Protocol></trt:Transport>'
                f'</trt:StreamSetup><trt:ProfileToken>{token}</trt:ProfileToken></trt:GetStreamUri>',
            )
            stream_uri = _safe_stream_uri(_text(uri_xml, "Uri"))
        except (httpx.HTTPError, ET.ParseError):
            pass
        channels.append({
            "channel_number": index,
            "name": name,
            "profile_token": token,
            "stream_uri": stream_uri,
            "status": "discovered",
        })
    return AdapterResult(
        reachable=True, adapter="onvif", manufacturer=_text(capabilities, "Manufacturer"),
        model=_text(capabilities, "Model"), channels=channels,
        capabilities=["onvif", "profiles", "rtsp_uri" if any(c["stream_uri"] for c in channels) else "profiles_only"],
        warnings=[],
    )


async def _hikvision_probe(
    client: httpx.AsyncClient, base: str, username: str, password: str
) -> AdapterResult:
    auth = httpx.DigestAuth(username, password)
    info = await client.get(base.rstrip("/") + "/ISAPI/System/deviceInfo", auth=auth)
    info.raise_for_status()
    root = ET.fromstring(info.content)
    channels: list[dict[str, Any]] = []
    warnings: list[str] = []
    for path in (
        "/ISAPI/ContentMgmt/InputProxy/channels",
        "/ISAPI/Streaming/channels",
    ):
        try:
            response = await client.get(base.rstrip("/") + path, auth=auth)
            response.raise_for_status()
            channel_root = ET.fromstring(response.content)
            for node in channel_root.iter():
                if _local(node.tag) in ("InputProxyChannel", "StreamingChannel") and len(channels) < 128:
                    number = _text(node, "id") or _text(node, "channelID") or str(len(channels) + 1)
                    channels.append({
                        "channel_number": int(number) if number.isdigit() else len(channels) + 1,
                        "name": _text(node, "name") or f"Channel {number}",
                        "profile_token": None, "stream_uri": None, "status": "discovered",
                    })
            if channels:
                break
        except (httpx.HTTPError, ET.ParseError, ValueError):
            continue
    if not channels:
        warnings.append("Hikvision channel endpoint did not return channels; ONVIF fallback may be available")
    return AdapterResult(
        reachable=True, adapter="hikvision_isapi", manufacturer=_text(root, "manufacturer") or "Hikvision",
        model=_text(root, "model"), channels=channels,
        capabilities=["hikvision_isapi", "device_info"] + (["channels"] if channels else []),
        warnings=warnings,
    )


async def _dahua_probe(
    client: httpx.AsyncClient, base: str, username: str, password: str
) -> AdapterResult:
    auth = httpx.DigestAuth(username, password)
    info = await client.get(base.rstrip("/") + "/cgi-bin/magicBox.cgi?action=getSystemInfo", auth=auth)
    info.raise_for_status()
    text = info.text
    model_match = re.search(r"(?im)^deviceType=(.+)$", text)
    channels_response = await client.get(
        base.rstrip("/") + "/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle",
        auth=auth,
    )
    channels: dict[int, str] = {}
    if channels_response.is_success:
        for line in channels_response.text.splitlines():
            match = re.search(r"ChannelTitle\[(\d+)\]\.Name=(.*)", line)
            if match and len(channels) < 128:
                channels[int(match.group(1)) + 1] = match.group(2).strip() or f"Channel {int(match.group(1)) + 1}"
    return AdapterResult(
        reachable=True, adapter="dahua_cgi", manufacturer="Dahua",
        model=model_match.group(1).strip() if model_match else None,
        channels=[
            {"channel_number": number, "name": name, "profile_token": None, "stream_uri": None, "status": "discovered"}
            for number, name in sorted(channels.items())
        ],
        capabilities=["dahua_cgi", "device_info"] + (["channels"] if channels else []),
        warnings=[] if channels else ["Dahua channel-title endpoint returned no channel names; try ONVIF profiles"],
    )


def _merge_onvif_streams(vendor_result: AdapterResult, onvif_result: AdapterResult) -> AdapterResult:
    for index, channel in enumerate(vendor_result.channels):
        if index < len(onvif_result.channels):
            onvif_channel = onvif_result.channels[index]
            channel["profile_token"] = onvif_channel.get("profile_token")
            channel["stream_uri"] = onvif_channel.get("stream_uri")
    vendor_result.capabilities.extend(
        capability for capability in onvif_result.capabilities
        if capability not in vendor_result.capabilities
    )
    vendor_result.warnings.extend(onvif_result.warnings)
    return vendor_result


class RecorderAdapterRegistry:
    """Brand-aware adapter selection with ONVIF fallback; credentials stay in memory only."""

    async def discover(
        self, host: str, port: int | None, brand: str, username: str, password: str
    ) -> AdapterResult:
        brand_key = brand.casefold()
        warnings: list[str] = []
        async with httpx.AsyncClient(timeout=8.0, verify=True, follow_redirects=False) as client:
            for base in _base_urls(host, port):
                try:
                    if "hikvision" in brand_key:
                        try:
                            vendor_result = await _hikvision_probe(client, base, username, password)
                            if vendor_result.channels:
                                try:
                                    onvif_result = await _onvif_discover(client, base, username, password)
                                    return _merge_onvif_streams(vendor_result, onvif_result)
                                except (httpx.HTTPError, ET.ParseError, ValueError):
                                    vendor_result.warnings.append("ONVIF media profiles unavailable; vendor channel inventory is still available")
                                    return vendor_result
                            warnings.extend(vendor_result.warnings)
                            warnings.append("Trying ONVIF profile discovery for Hikvision recorder")
                        except (httpx.HTTPError, ET.ParseError, ValueError):
                            warnings.append("Hikvision ISAPI unavailable; trying ONVIF")
                    elif "dahua" in brand_key:
                        try:
                            vendor_result = await _dahua_probe(client, base, username, password)
                            if vendor_result.channels:
                                try:
                                    onvif_result = await _onvif_discover(client, base, username, password)
                                    return _merge_onvif_streams(vendor_result, onvif_result)
                                except (httpx.HTTPError, ET.ParseError, ValueError):
                                    vendor_result.warnings.append("ONVIF media profiles unavailable; vendor channel inventory is still available")
                                    return vendor_result
                            warnings.extend(vendor_result.warnings)
                            warnings.append("Trying ONVIF profile discovery for Dahua recorder")
                        except (httpx.HTTPError, ET.ParseError, ValueError):
                            warnings.append("Dahua CGI unavailable; trying ONVIF")
                    try:
                        result = await _onvif_discover(client, base, username, password)
                        result.warnings.extend(warnings)
                        return result
                    except (httpx.HTTPError, ET.ParseError, ValueError):
                        continue
                except httpx.HTTPError:
                    continue
        return AdapterResult(
            reachable=False, adapter="none", manufacturer=None, model=None,
            channels=[], capabilities=[], warnings=warnings + [
                "No supported authenticated HTTP/ONVIF service responded. Check reachability, port, credentials and device protocol."
            ],
        )


registry = RecorderAdapterRegistry()
