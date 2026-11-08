# Authentication, roles and tenant isolation

## First-time setup

Set a high-entropy one-time secret in the backend environment before the first
bootstrap:

`MOLIDO_CCTV_BOOTSTRAP_SECRET=<generated-secret>`

The secret is read from the server environment and is never stored in the
repository. Call `POST /api/v1/auth/bootstrap` once with the secret in the
`X-Bootstrap-Secret` header and a manager email, password, tenant name and
tenant slug. Bootstrap fails if the secret is missing or incorrect, and it
cannot create a second initial account after a user already exists. There is no
default username or password. Remove the bootstrap secret from the environment
after successful initialization.

## Authentication API

- `POST /api/v1/auth/login`: email, password and tenant slug; returns an
  opaque one-hour bearer token.
- `GET /api/v1/auth/me`: current account, tenant and role.
- `POST /api/v1/auth/logout`: revokes the current session.
- `POST /api/v1/auth/users`: manager-only account creation for manager,
  employee or viewer roles.

All `/api/v1/*` endpoints require a valid bearer session except health,
bootstrap, login and the private MediaMTX callback. The session token is
returned once; only its SHA-256 hash is persisted. Passwords use salted
PBKDF2-HMAC-SHA256 hashes. Eight failed attempts in a five-minute window lock
the identity for fifteen minutes.

## Roles

| Role | Camera/device read | Camera/device changes | Live view | Manage users |
|---|---:|---:|---:|---:|
| Manager | Yes | Yes | Yes | Yes |
| Employee | Yes | Yes | Yes | No |
| Viewer | Yes | No | Yes | No |

Viewer write requests are rejected with HTTP 403. User management is restricted
to managers. The current API authorization policy is enforced centrally by
middleware so newly added `/api/v1` routes are protected by default.

## Tenant isolation

A bearer session is bound to one tenant membership. Supplying a different
`X-Tenant-ID` is rejected. Inventory requests run against a separate SQLite
database file under `data/tenants/<tenant-id>/cameras.sqlite3`; authentication,
memberships and sessions remain in the central authentication database. This
prevents one tenant's camera, recorder and channel rows from appearing in
another tenant's API responses.

## Operational security

- Serve the API only over HTTPS outside a private local network.
- Keep the bootstrap secret and database files out of source control.
- Back up the central authentication database and each tenant database.
- Restrict filesystem permissions on all database directories.
- Use a dedicated deployment secret manager; never put passwords in source,
  logs, URLs or Android source code.
- The MediaMTX callback has a separate disabled-by-default switch and source
  CIDR allowlist; see [MediaMTX authentication](mediamtx-authentication.md).

The existing camera inventory predating tenant setup is not automatically
assigned to a tenant by this change. Before migrating a populated installation,
take a backup and explicitly assign the legacy rows to the intended first
tenant; do not copy unscoped records into every tenant database.

## Android client

The Flutter client includes a four-language sign-in screen, tenant slug selection,
session validation on app start, sign-out/revocation, and a manager-only account
creation form for all three roles. Bearer tokens are stored with
`flutter_secure_storage` rather than ordinary preferences. Android backup is
disabled, and cleartext networking is restricted to the Android emulator host
`10.0.2.2`; non-emulator server URLs must use HTTPS.
