# Dahua official API/SDK access request

## Status

This document prepares the official access request. It does **not** mean that Dahua has approved an account, issued credentials, granted SDK access, or confirmed DMSS-compatible third-party P2P support.

## Recommended access route

1. Create a developer account at https://open.dolynkcloud.com/ using an email controlled by the project owner (a company email is preferable).
2. Complete the company authentication requested by the portal. Dahua states that company authentication unlocks full platform capabilities and production access.
3. In the developer console, request the API/SDK documentation, application credentials, sandbox/test access, and production onboarding applicable to the company's country/region.
4. Separately ask Dahua to confirm in writing whether its authorized third-party SDK/API supports the **same serial-number + recorder-admin-credentials remote P2P workflow used by consumer DMSS**, for third-party Android apps. Do not assume DoLynk Developer is equivalent to DMSS consumer P2P.
5. Obtain written confirmation of supported device families, model/firmware constraints, regions, licensing, quotas, security requirements, and technical support contacts before enabling the adapter.

Official portals:
- DoLynk Developer: https://open.dolynkcloud.com/
- Dahua API portal: https://www.dahuasecurity.com/api/
- Dahua software/SDK download center: https://www.dahuasecurity.com/download-center/softwares
- Dahua DoLynk Developer overview: https://www.dahuasecurity.com/products/software/dolynk-cloud/doylnk-product/eco

## Information the account owner must provide

Do not commit these details or credentials to Git:
- Legal company name and country/region of registration.
- Company website and business contact details.
- Authorized representative/contact name and company email.
- Business registration/tax documentation if requested by Dahua.
- Intended deployment countries/regions and estimated number of devices/users.
- Whether the requested integration is cloud-based DoLynk Developer, on-premises DSS API/SDK, or both.

Never send account passwords, API secrets, private keys, recorder passwords, or customer device serial lists in ordinary email or chat. Use Dahua's authenticated portal or an approved secure channel.

## Draft request to Dahua (English)

**Subject:** Request for official Dahua API/SDK access and third-party Android P2P integration guidance

Hello Dahua Developer / Technical Support Team,

We are developing **Molido CCTV AI**, a third-party Android-first video management application with a FastAPI backend. Our initial device integration target is Dahua DVR/NVR/XVR equipment.

We would like to apply for the appropriate official developer access and request guidance on the following:

1. DoLynk Developer API/SDK access for device management, cloud live view, playback, channel information, device status, and alarm/event notifications.
2. Whether an officially supported third-party SDK/API is available for the consumer DMSS-style remote P2P onboarding flow (device serial number/QR plus the recorder's own username and password), without requiring the end user to share a DMSS account.
3. Whether the above P2P integration is supported for third-party Android applications, and which device models, firmware versions, countries/regions, and device/account modes are supported.
4. Whether an on-premises DSS API/SDK is a better-supported route for a third-party VMS, and the applicable API/SDK package and licensing terms.
5. Developer registration, company verification, sandbox access, API credential issuance, SDK download, technical documentation, security review, and production approval steps.
6. Any commercial, certification, minimum-volume, or partner requirements.

Please direct us to the correct developer program and provide the official onboarding checklist and technical contact for our region.

We will use only authorized Dahua interfaces and will protect all application credentials and end-user device credentials. We will not reverse-engineer private DMSS protocols or reuse private DMSS session tokens.

Company details:
- Legal company name: [to be completed by account owner]
- Country/region: [to be completed]
- Company website: [to be completed]
- Authorized contact: [to be completed]
- Business email: [to be completed]
- Estimated deployment scale: [to be completed]

Thank you,
Molido CCTV AI Development Team

## Integration gate in Molido

Do not enable live cloud sessions until all of the following are true:
- Dahua has confirmed the supported product/API path in writing.
- The project has accepted the applicable license/terms.
- Official SDK/API documentation and test credentials have been obtained.
- Backend authentication, tenant/user/device authorization, secret storage, audit logging, and short-lived stream-session authorization have passed review.
- The target device model/firmware/region has been physically tested.

Until then, the adapter remains disabled and the app must continue to report that live cloud video is not configured. No fake online status or playback URL is permitted.
