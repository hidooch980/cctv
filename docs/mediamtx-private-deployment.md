# MediaMTX private deployment template

This is a deployment scaffold, not a live deployment. It creates a non-root
FastAPI container and a MediaMTX container on a dedicated internal Docker
network. MediaMTX can reach the FastAPI auth callback at `http://api:8000`;
the callback allowlist is restricted to the MediaMTX container address
`172.30.40.3/32`. No MediaMTX listener or control API is published to the host.

## Before starting

1. Copy this directory's compose example to a reviewed deployment location.
2. Pin `MEDIAMTX_IMAGE` to a tested immutable digest, not a floating tag.
3. Provide a high-entropy one-time `MOLIDO_CCTV_BOOTSTRAP_SECRET` through the
   host's secret manager/environment; never commit it.
4. Keep both MediaMTX flags false until the API and gateway have been deployed,
   network-tested, and reviewed.
5. Keep API port 8000 bound to loopback and put a TLS reverse proxy in front.
6. Configure only the required HLS/WebRTC listeners through a TLS/WSS proxy
   and firewall. WebRTC ICE/UDP requires a deliberate public/private network
   plan; do not expose the default port range blindly.
7. Provision each MediaMTX path and its upstream RTSP source through a
   reviewed server-side controller. Do not pass raw RTSP URLs or recorder
   credentials to Android.
8. Back up `cctv-data` securely and test restore before production.

The example deliberately does not publish any media ports and does not turn
on playback token issuance. A successful token callback alone does not prove
that a path exists or that a camera stream is playable.
