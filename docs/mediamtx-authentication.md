# MediaMTX external authentication

## Implemented control-plane contract

The FastAPI callback is `POST /api/v1/media/mediamtx/auth`. It follows MediaMTX's
external HTTP authentication payload and accepts only a short-lived opaque
credential in `token` (or `password`), with all of these constraints:

- exact media path match;
- action `read` only;
- protocol `hls` or `webrtc` only;
- unexpired token and unexpired, non-revoked parent user session;
- active user and session-bound tenant;
- callback source IP inside `MOLIDO_CCTV_MEDIAMTX_ALLOWED_CIDRS`.

Only a successful callback returns an RFC3339 `expireAt`. Empty credentials,
unknown paths, publish requests, RTSP credentials, revoked sessions and expired
tokens are rejected. No user password or recorder password is accepted as a
MediaMTX credential.

## Required private deployment settings

Set these only after the API and MediaMTX share a private network:

- `MOLIDO_CCTV_MEDIAMTX_ENABLED=true`
- `MOLIDO_CCTV_MEDIAMTX_ALLOWED_CIDRS=<exact-private-subnet>`

Leave the feature disabled if the allowlist is empty. Do not use `0.0.0.0/0`,
public client ranges, or a public reverse-proxy address as the allowlist.
Restrict the callback path at the reverse proxy/firewall as well. Do not expose
the MediaMTX Control API, metrics, or pprof publicly.

Use `deploy/mediamtx.yml.example` as a starting point, not as a production
deployment. Keep the callback address on the private service network, use TLS
for any network segment that is not a trusted local bridge, and publish HLS /
WebRTC listeners only through a reviewed firewall and HTTPS/WSS reverse proxy.
Keep `authHTTPExclude` empty.

## Not yet enabled

The callback and path/session-bound token verifier are implemented and tested
as backend code. The application does **not** yet issue production playback
tokens from a validated stream session, configure MediaMTX paths from recorder
RTSP sources, deploy a MediaMTX process, or pass a real gateway handshake.
The stream-session API therefore remains fail-closed and live view remains
disabled. Do not set the enable flag in production until the remaining token
issuer, source/path provisioning, network policy and end-to-end tests are
completed.
