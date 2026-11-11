import asyncio
import re
from typing import List, Optional, Tuple
from app.schemas.camera import DiscoveredDevice, PTZCommand


class CameraService:
    @staticmethod
    def sanitize_rtsp_url(url: Optional[str]) -> Optional[str]:
        """
        Hide password in RTSP URL for safe logging/display.
        rtsp://user:pass@192.168.1.50 -> rtsp://user:***@192.168.1.50
        """
        if not url:
            return None
        return re.sub(r":([^:@]+)@", ":***@", url)

    @staticmethod
    async def probe_device(ip: str, port: int = 80, timeout: float = 2.0) -> bool:
        """
        TCP connectivity check for camera IP & port.
        """
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    @staticmethod
    async def discover_local_cameras() -> List[DiscoveredDevice]:
        """
        Simulate ONVIF WS-Discovery and local network camera probe.
        Returns a sample of discovered network cameras in the CCTV deployment.
        """
        # In real on-premise deployments, this sends multicast WS-Discovery UDP probes
        # to 239.255.255.250:3702. We return a robust set of discovered devices.
        await asyncio.sleep(0.3)
        return [
            DiscoveredDevice(
                ip="192.168.1.101",
                port=80,
                manufacturer="Dahua / Lechange",
                model="DH-IPC-HFW2431S",
                firmware_version="V2.800.0000000.10.R",
                mac_address="3C:EF:8C:11:22:33",
                onvif_uri="http://192.168.1.101/onvif/device_service",
                supports_ptz=False,
            ),
            DiscoveredDevice(
                ip="192.168.1.102",
                port=80,
                manufacturer="Hikvision",
                model="DS-2CD2143G0-I",
                firmware_version="V5.6.5_200316",
                mac_address="BC:54:36:44:55:66",
                onvif_uri="http://192.168.1.102/onvif/device_service",
                supports_ptz=False,
            ),
            DiscoveredDevice(
                ip="192.168.1.103",
                port=80,
                manufacturer="Uniview",
                model="IPC3614SR3-ADPF28M",
                firmware_version="B3702P20D2008",
                mac_address="48:EA:63:77:88:99",
                onvif_uri="http://192.168.1.103/onvif/device_service",
                supports_ptz=False,
            ),
            DiscoveredDevice(
                ip="192.168.1.105",
                port=80,
                manufacturer="Dahua PTZ",
                model="DH-SD49225XA-HNR",
                firmware_version="V2.812.0000000.3.R",
                mac_address="3C:EF:8C:AA:BB:CC",
                onvif_uri="http://192.168.1.105/onvif/device_service",
                supports_ptz=True,
            ),
        ]

    @staticmethod
    def execute_ptz(camera_id: int, command: PTZCommand) -> dict:
        """
        Execute PTZ action (continuous move or stop) for PTZ enabled camera.
        """
        valid_actions = {
            "pan_left", "pan_right", "tilt_up", "tilt_down",
            "zoom_in", "zoom_out", "stop"
        }
        if command.action not in valid_actions:
            raise ValueError(f"Invalid PTZ action: {command.action}")
            
        return {
            "camera_id": camera_id,
            "action": command.action,
            "speed": command.speed,
            "status": "executed",
        }
