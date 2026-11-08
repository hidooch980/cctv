# Android release signing and updates

## Signed release

The release workflow builds a **signed release APK**, verifies its APK signature with Android `apksigner`, calculates SHA-256, and publishes both files to a GitHub Release. It runs manually from Actions or when a `v*` tag is pushed.

Create a dedicated Android release keystore once and keep a secure offline backup. Losing it prevents future APKs from updating installations signed with that key. Never commit the keystore or `key.properties`.

Add these four repository Actions secrets under **Settings → Secrets and variables → Actions**:

- `ANDROID_KEYSTORE_BASE64`: base64 encoding of the JKS/PKCS12 keystore file
- `ANDROID_KEY_ALIAS`: key alias
- `ANDROID_KEY_PASSWORD`: private-key password
- `ANDROID_STORE_PASSWORD`: keystore password

The workflow intentionally fails if any secret is missing. It never publishes an unsigned or debug APK as a release.

## Triggering a release

After the branch is merged into the default branch, create and push a version tag such as `v0.1.0`, or run **Actions → Android signed release → Run workflow** on the intended branch and enter a tag. Increase `version:` in `mobile/pubspec.yaml` before each release (both version name and build number must increase).

## App update behavior

GitHub Releases is the release feed and APK distribution source. Android does not permit an ordinary app to silently replace itself. The supported sideload update flow is: app checks the latest release, informs the user, downloads the signed APK, then asks Android's package installer to complete installation; the user may need to allow installs from this app. For fully managed silent updates, distribute through managed Google Play / Android Enterprise or a device-owner MDM.

The Android client now checks GitHub Releases on startup and includes a manual **Automatic updates** check in Settings. When a newer version exists, it offers the signed APK asset (or the release page) for download. Android then requires the user to confirm installation; this is not a silent background installer. The update checker currently compares the release tag with the app version constant in `mobile/lib/main.dart`, so update that constant and `mobile/pubspec.yaml` together for every release. Updates must be signed with the same keystore and use the same Android application ID. Real-device testing of download and package installation is still required.
