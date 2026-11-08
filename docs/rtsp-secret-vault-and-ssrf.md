# RTSP secret vault and SSRF policy

## Status
This commit adds tested security primitives only. It does not yet persist source
records, provision MediaMTX paths, initiate network connections, or enable playback.

## Secret handling
- AES-256-GCM authenticated encryption; 96-bit random nonce per encryption.
- Key is supplied out-of-band through `MOLIDO_CCTV_RTSP_VAULT_KEY` as URL-safe
  base64 encoding of exactly 32 random bytes.
- Never commit the key, place it in the database, return encrypted envelopes to
  clients, or log plaintext credentials.
- Encryption context must include immutable tenant and recorder identifiers.
  This binds ciphertext to its intended record and prevents cross-tenant swaps.
- Key rotation requires decrypt/re-encrypt migration with a separately protected
  old key; losing the key makes stored credentials unrecoverable.

## SSRF and DNS rebinding
- Only `rtsp://` and `rtsps://`; credentials are separate secret fields.
- URI query and fragment are rejected.
- Every resolved IPv4/IPv6 address must be inside an explicitly configured
  `MOLIDO_CCTV_RTSP_ALLOWED_CIDRS` allowlist. Loopback, link-local, multicast,
  unspecified and reserved destinations are rejected.
- Private camera networks are allowed only by explicitly adding their exact
  subnets, e.g. `10.20.0.0/24`; do not use `0.0.0.0/0`.
- Validate again immediately before MediaMTX provisioning and pin the validated
  resolved IP for the upstream connection. Do not resolve once at registration
  and later connect by hostname: that permits DNS rebinding.
- Redirects and arbitrary URL fetches are not part of this flow.

## Required next integration
1. Add tenant-scoped encrypted source rows and manager/employee-only create/update.
2. Resolve and validate destinations at save and again at connection time.
3. Provision paths through MediaMTX Control API on a private service network only.
4. Keep Control API inaccessible from Android/public internet.
5. Issue session-, tenant-, channel-, profile- and transport-bound short-lived
   playback tokens. Do not expose RTSP URIs or secrets to the mobile client.
6. Add gateway integration tests and real-device acceptance before enabling playback.
