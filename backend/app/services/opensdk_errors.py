"""
OpenSDK Error Code Registry & Automated Resolution Engine
Based on Dahua / Lechange / Imou OpenSDK Development Guide Specification.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class ErrorResolution(BaseModel):
    code: str
    numeric_code: Optional[int] = None
    category: str
    name: str
    description_en: str
    description_fa: str
    probable_cause_en: str
    probable_cause_fa: str
    recommended_action_en: str
    recommended_action_fa: str
    recovery_strategy: str  # retry_backoff, reauth, fallback_substream, p2p_reconnect, check_network, admin_intervention


OPENSDK_ERROR_CATALOG: Dict[str, Dict[str, Any]] = {
    # RTSP Streaming Errors
    "STATE_RTSP_AUTHORIZATION_FAIL": {
        "numeric_code": 401,
        "category": "RTSP Protocol",
        "name": "RTSP Authorization Failure",
        "description_en": "Camera RTSP authentication failed (HTTP/RTSP 401 Unauthorized).",
        "description_fa": "احراز هویت استریم RTSP دوربین ناموفق بود (کد 401 غیرمجاز).",
        "probable_cause_en": "Incorrect camera username or password, expired token, or digest auth mismatch.",
        "probable_cause_fa": "نام کاربری یا رمز عبور دوربین اشتباه است، یا توکن منقضی شده است.",
        "recommended_action_en": "Verify camera credentials in inventory, refresh device access token, or re-enter device password.",
        "recommended_action_fa": "اطلاعات ورود دوربین را بررسی کرده و توکن دسترسی را تجدید کنید.",
        "recovery_strategy": "reauth",
    },
    "STATE_RTSP_SERVICE_UNAVAILABLE": {
        "numeric_code": 503,
        "category": "RTSP Protocol",
        "name": "RTSP Service Unavailable / Max Connections Reached",
        "description_en": "Camera RTSP service unavailable. Often hit when maximum concurrent stream sessions (503) are reached.",
        "description_fa": "سرویس RTSP در دسترس نیست؛ سقف اتصالات همزمان دوربین پر شده است (503).",
        "probable_cause_en": "Too many clients viewing live feed simultaneously, or camera encoder overloaded.",
        "probable_cause_fa": "تعداد درخواست‌های استریم همزمان بیش از ظرفیت سخت‌افزاری دوربین است.",
        "recommended_action_en": "Close idle sessions, switch clients to sub-stream (lower bitrate/resolution), or route streams through media proxy.",
        "recommended_action_fa": "جلسات غیرفعال را ببندید، کلاینت‌ها را به Sub-stream تغییر دهید یا از پروکسی مدیا استفاده کنید.",
        "recovery_strategy": "fallback_substream",
    },
    "STATE_RTSP_KEY_MISMATCH": {
        "numeric_code": 403,
        "category": "RTSP Encryption",
        "name": "RTSP Stream Decryption Key Mismatch",
        "description_en": "Stream decryption key does not match device encryption key.",
        "description_fa": "کلید رمزگشایی جریان با کلید رمزنگاری دستگاه مطابقت ندارد.",
        "probable_cause_en": "Device video encryption is enabled on camera/NVR and client provided wrong key.",
        "probable_cause_fa": "قابلیت رمزنگاری ویدیو روی دستگاه فعال است و کلید ارائه‌شده اشتباه است.",
        "recommended_action_en": "Provide the valid device verification code (safety code on device sticker).",
        "recommended_action_fa": "کد تأیید یا رمزنگاری دستگاه (روی برچسب دستگاه) را در تنظیمات وارد کنید.",
        "recovery_strategy": "reauth",
    },
    "STATE_RTSP_TEARDOWN_ERROR": {
        "numeric_code": 500,
        "category": "RTSP Protocol",
        "name": "RTSP Teardown Error",
        "description_en": "Error occurred while tearing down the RTSP session.",
        "description_fa": "خطا هنگام بستن و پایان نشست RTSP رخ داد.",
        "probable_cause_en": "Network socket timed out before camera acknowledged TEARDOWN packet.",
        "probable_cause_fa": "اتصال شبکه قبل از تأیید بسته پایان نشست قطع شد.",
        "recommended_action_en": "Force-close client socket, release play window handle and allocate fresh handle.",
        "recommended_action_fa": "سوکت قبلی را به اجبار آزاد کرده و پنجره پخش را مجدداً مقداردهی نمایید.",
        "recovery_strategy": "retry_backoff",
    },
    "STATE_PACKET_FRAME_ERROR": {
        "numeric_code": 502,
        "category": "RTSP Stream Quality",
        "name": "Packet Frame Corruption / Missing P-Frames",
        "description_en": "Decoded packet frame corruption or packet loss threshold exceeded.",
        "description_fa": "خرابی فریم‌های ویدیویی یا افت شدید بسته‌های شبکه در استریم.",
        "probable_cause_en": "Unstable network connection, high packet loss, or excessive MTU fragmentation.",
        "probable_cause_fa": "ناپایداری شبکه، افت بسته (Packet Loss) یا تداخل پهنای باند.",
        "recommended_action_en": "Switch transport to RTSP-over-TCP, reduce camera bitrate or FPS.",
        "recommended_action_fa": "پروتکل انتقال را به TCP تغییر دهید و بیت‌ریت دوربین را تعدیل کنید.",
        "recovery_strategy": "retry_backoff",
    },

    # DHHTTP (Dahua HTTP / Cloud Protocol)
    "STATE_DHHTTP_SERVER_ERROR": {
        "numeric_code": 503001,
        "category": "DHHTTP Cloud",
        "name": "DHHTTP Cloud Server Disconnect",
        "description_en": "Server directly disconnected the stream due to server error / limit reached (503001).",
        "description_fa": "سرور ابری ارتباط استریم را به دلیل خطای سرور یا تکمیل ظرفیت قطع کرد (503001).",
        "probable_cause_en": "PaaS / Cloud relay server overloaded or connection pool exhausted.",
        "probable_cause_fa": "سرور واسط ابری دارای بار ترافیکی بیش از حد است.",
        "recommended_action_en": "Trigger P2P hole-punching fallback or switch to direct LAN RTSP connection.",
        "recommended_action_fa": "به اتصال مستقیم محلی RTSP یا ارتباط P2P بازگشت نمایید.",
        "recovery_strategy": "p2p_reconnect",
    },
    "STATE_DHHTTP_CLIENT_ERROR": {
        "numeric_code": 1000000,
        "category": "DHHTTP Client",
        "name": "DHHTTP Client Internal Logic Error",
        "description_en": "Internal client logic error in OpenApiClient (1000000).",
        "description_fa": "خطای منطقی کلاینت درون OpenApiClient (کد 1000000).",
        "probable_cause_en": "Uninitialized player surface, invalid channel index, or null token pointer.",
        "probable_cause_fa": "عدم مقداردهی اولیه Surface پنجره پخش یا اشتباه در شماره کانال.",
        "recommended_action_en": "Ensure initPlayWindow() is called before starting stream; check channel index.",
        "recommended_action_fa": "مطمئن شوید متد initPlayWindow قبل از آغاز استریم فراخوانی شده است.",
        "recovery_strategy": "retry_backoff",
    },
    "DEC_KEY_ERROR": {
        "numeric_code": 403002,
        "category": "Decoder",
        "name": "Stream Decryption Key Incorrect",
        "description_en": "H.264/H.265 video stream payload cannot be decrypted with given key.",
        "description_fa": "کلید رمزگشایی جریان ویدیویی نامعتبر است و ویدیو دیکد نمی‌شود.",
        "probable_cause_en": "Encrypted video option enabled on device, verification code changed.",
        "probable_cause_fa": "رمزنگاری ویدیوی دستگاه فعال است یا کد اعتبارسنجی تغییر کرده است.",
        "recommended_action_en": "Update decryption key in OpenSDK_PlayWindow via setStreamCallback/decryptKey.",
        "recommended_action_fa": "کلید صحیح رمزگشایی را در تنظیمات پنجره نمایش تنظیم کنید.",
        "recovery_strategy": "reauth",
    },

    # Bluetooth & Access Control
    "BLUETOOTH_DISABLED": {
        "numeric_code": 1001,
        "category": "Access Control",
        "name": "Bluetooth Disabled",
        "description_en": "Mobile Bluetooth adapter is turned off.",
        "description_fa": "بلوتوث دستگاه خاموش است.",
        "probable_cause_en": "User or OS disabled Bluetooth radio.",
        "probable_cause_fa": "کاربر یا سیستم عامل بلوتوث را خاموش کرده است.",
        "recommended_action_en": "Prompt user to enable Bluetooth in device settings.",
        "recommended_action_fa": "از کاربر بخواهید بلوتوث گوشی را روشن کند.",
        "recovery_strategy": "admin_intervention",
    },
    "PERMISSION_DENIED": {
        "numeric_code": 1002,
        "category": "Access Control",
        "name": "Permissions Denied",
        "description_en": "BLUETOOTH_SCAN, BLUETOOTH_CONNECT or ACCESS_FINE_LOCATION permission not granted.",
        "description_fa": "مجوزهای دسترسی بلوتوث یا موقعیت مکانی صادر نشده است.",
        "probable_cause_en": "Android 12+ runtime permissions not accepted by user.",
        "probable_cause_fa": "مجوزهای امنیتی در اندروید توسط کاربر تایید نشده است.",
        "recommended_action_en": "Request BLUETOOTH_SCAN and BLUETOOTH_CONNECT runtime permissions.",
        "recommended_action_fa": "مجوزهای دسترسی مربوطه را از کاربر درخواست کنید.",
        "recovery_strategy": "admin_intervention",
    },
    "GATT_CONNECT_FAILED": {
        "numeric_code": 2001,
        "category": "Access Control",
        "name": "GATT Connection Failed",
        "description_en": "Failed to establish BLE GATT connection to access control terminal.",
        "description_fa": "برقراری ارتباط GATT بلوتوث با دستگاه اکسس کنترل ناموفق بود.",
        "probable_cause_en": "Terminal is out of BLE range, busy with another phone, or signal degraded.",
        "probable_cause_fa": "دستگاه خارج از برد بلوتوث است یا به دستگاه دیگری متصل است.",
        "recommended_action_en": "Move closer to terminal, retry scan, clear GATT cache.",
        "recommended_action_fa": "به دستگاه نزدیک‌تر شوید و اسکن مجدد را امتحان کنید.",
        "recovery_strategy": "retry_backoff",
    },
    "AUTH_FAILED": {
        "numeric_code": 3004,
        "category": "Access Control",
        "name": "Door Access Authentication Failed",
        "description_en": "Door opening cryptographic challenge failed.",
        "description_fa": "اعتبارسنجی بازگشایی درب با دستگاه ناموفق بود.",
        "probable_cause_en": "Expired door key credential, revoked permission, or clock drift.",
        "probable_cause_fa": "مجوز دسترسی منقضی شده یا دسترسی کاربر مسدود شده است.",
        "recommended_action_en": "Sync credentials with backend access control server.",
        "recommended_action_fa": "کلید دسترسی را با سرور پشتیبانی به‌روزرسانی کنید.",
        "recovery_strategy": "reauth",
    },
}


def resolve_opensdk_error(error_identifier: str) -> ErrorResolution:
    """
    Look up and resolve OpenSDK errors by name or code.
    """
    clean_id = str(error_identifier).strip().upper()
    
    # Direct lookup by name
    if clean_id in OPENSDK_ERROR_CATALOG:
        data = OPENSDK_ERROR_CATALOG[clean_id]
        return ErrorResolution(code=clean_id, **data)
    
    # Lookup by numeric code
    for key, data in OPENSDK_ERROR_CATALOG.items():
        if str(data.get("numeric_code")) == str(error_identifier):
            return ErrorResolution(code=key, **data)
            
    # Generic fallback
    return ErrorResolution(
        code=str(error_identifier),
        numeric_code=None,
        category="General / Unknown",
        name="Unknown OpenSDK Event",
        description_en=f"Uncataloged SDK status code: {error_identifier}",
        description_fa=f"کد وضعیت ناشناخته اس‌دی‌کی: {error_identifier}",
        probable_cause_en="Firmware vendor deviation, undocumented SDK error or unexpected network disconnect.",
        probable_cause_fa="خطای گزارش نشده در میان‌افزار یا قطع ارتباط غیرمنتظره شبکه.",
        recommended_action_en="Inspect device logs, verify RTSP stream with VLC/ffprobe, and check network reachability.",
        recommended_action_fa="لاگ‌های دستگاه را بررسی کنید و با ابزار ffprobe دسترسی به RTSP را بسنجید.",
        recovery_strategy="retry_backoff",
    )
