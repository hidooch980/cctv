# Android release signing

The debug APK is for internal testing only. A production release must be signed with an organization-controlled Android upload/release keystore.

## Required GitHub Actions secrets

Configure these repository secrets before manually dispatching **Android signed release**:

- `ANDROID_KEYSTORE_BASE64`: base64-encoded JKS/PKCS12 keystore file.
- `ANDROID_KEY_ALIAS`: key alias.
- `ANDROID_KEY_PASSWORD`: private-key password.
- `ANDROID_STORE_PASSWORD`: keystore password.

Generate and back up the keystore securely outside this repository. Never commit the keystore, `key.properties`, passwords, or signing material. Restrict secret access and preserve the keystore backup; losing it can prevent future updates signed with the same app identity.

## Build flow

The release workflow generates the Flutter Android platform scaffold, configures Gradle signing from Actions secrets, runs analysis and widget tests, builds a release APK, and attaches it to a GitHub Release. The workflow is intentionally skipped until all four secrets exist.

## Device and production validation still required

- Install the release APK on supported physical Android devices.
- Verify server URL, authentication, TLS certificate validation, and camera network reachability.
- Verify ONVIF discovery and RTSP playback against authorized camera models.
- Run sustained multi-stream tests with representative bitrate/resolution and server hardware.
- Configure app signing identity, privacy policy, retention, backup, monitoring, and incident response before production rollout.
