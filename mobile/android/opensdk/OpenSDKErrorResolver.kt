package com.molido.cctv.opensdk

import android.util.Log

/**
 * OpenSDK Error Resolver & Diagnostics Engine
 * Maps OpenSDK player results, RTSP status codes, DHHTTP cloud codes, and BLE access errors
 * into actionable recovery actions for Molido CCTV Mobile Client.
 *
 * Based on Android OpenSDK Development Guide V3.8.0 specification.
 */
enum class OpenSDKRecoveryStrategy {
    RETRY_BACKOFF,
    REAUTHENTICATE,
    FALLBACK_SUBSTREAM,
    P2P_RECONNECT,
    REQUEST_PERMISSIONS,
    ENABLE_BLUETOOTH,
    NOTIFY_OPERATOR
}

data class OpenSDKErrorDetails(
    val code: String,
    val numericCode: Int?,
    val category: String,
    val messageEn: String,
    val messageFa: String,
    val recoveryStrategy: OpenSDKRecoveryStrategy,
    val actionSuggestion: String
)

object OpenSDKErrorResolver {
    private const val TAG = "OpenSDKErrorResolver"

    fun resolve(errorCode: String): OpenSDKErrorDetails {
        return when (errorCode.uppercase()) {
            "STATE_RTSP_AUTHORIZATION_FAIL", "401" -> OpenSDKErrorDetails(
                code = "STATE_RTSP_AUTHORIZATION_FAIL",
                numericCode = 401,
                category = "RTSP Auth",
                messageEn = "Camera RTSP authentication failed (401 Unauthorized)",
                messageFa = "احراز هویت استریم دوربین ناموفق بود (کد 401)",
                recoveryStrategy = OpenSDKRecoveryStrategy.REAUTHENTICATE,
                actionSuggestion = "Refresh device token or re-enter valid camera password in device settings."
            )
            "STATE_RTSP_SERVICE_UNAVAILABLE", "503" -> OpenSDKErrorDetails(
                code = "STATE_RTSP_SERVICE_UNAVAILABLE",
                numericCode = 503,
                category = "RTSP Stream Limit",
                messageEn = "Camera max concurrent RTSP streams reached (503)",
                messageFa = "سقف اتصالات همزمان دوربین پر شده است (503)",
                recoveryStrategy = OpenSDKRecoveryStrategy.FALLBACK_SUBSTREAM,
                actionSuggestion = "Switch player to sub-stream (subType=1) to conserve camera encoder bandwidth."
            )
            "STATE_DHHTTP_SERVER_ERROR", "503001" -> OpenSDKErrorDetails(
                code = "STATE_DHHTTP_SERVER_ERROR",
                numericCode = 503001,
                category = "Cloud Relay",
                messageEn = "Cloud relay server disconnected due to high load (503001)",
                messageFa = "سرور ابری ارتباط را به دلیل بار ترافیکی قطع کرد (503001)",
                recoveryStrategy = OpenSDKRecoveryStrategy.P2P_RECONNECT,
                actionSuggestion = "Fallback to direct P2P hole-punching or local LAN RTSP stream."
            )
            "DEC_KEY_ERROR", "403002" -> OpenSDKErrorDetails(
                code = "DEC_KEY_ERROR",
                numericCode = 403002,
                category = "Decoder Encryption",
                messageEn = "Stream decryption key incorrect or missing",
                messageFa = "کلید رمزگشایی ویدیو اشتباه است",
                recoveryStrategy = OpenSDKRecoveryStrategy.REAUTHENTICATE,
                actionSuggestion = "Input device safety verification code from camera label into decryptKey."
            )
            "STATE_PACKET_FRAME_ERROR", "502" -> OpenSDKErrorDetails(
                code = "STATE_PACKET_FRAME_ERROR",
                numericCode = 502,
                category = "Network Stream",
                messageEn = "Packet loss threshold exceeded or missing video I/P-frames",
                messageFa = "افت شدید بسته شبکه یا خرابی فریم‌های ویدیویی",
                recoveryStrategy = OpenSDKRecoveryStrategy.RETRY_BACKOFF,
                actionSuggestion = "Switch transport protocol to TCP and reduce stream bitrate."
            )
            // Bluetooth Access Control Errors
            "BLUETOOTH_DISABLED", "1001" -> OpenSDKErrorDetails(
                code = "BLUETOOTH_DISABLED",
                numericCode = 1001,
                category = "BLE Access",
                messageEn = "Device Bluetooth is disabled",
                messageFa = "بلوتوث گوشی خاموش است",
                recoveryStrategy = OpenSDKRecoveryStrategy.ENABLE_BLUETOOTH,
                actionSuggestion = "Prompt user with EnableBluetooth Intent."
            )
            "PERMISSION_DENIED", "1002" -> OpenSDKErrorDetails(
                code = "PERMISSION_DENIED",
                numericCode = 1002,
                category = "BLE Access",
                messageEn = "Bluetooth / Location permissions not granted",
                messageFa = "مجوزهای دسترسی بلوتوث یا موقعیت مکانی صادر نشده است",
                recoveryStrategy = OpenSDKRecoveryStrategy.REQUEST_PERMISSIONS,
                actionSuggestion = "Request BLUETOOTH_SCAN and BLUETOOTH_CONNECT runtime permissions."
            )
            "GATT_CONNECT_FAILED", "2001" -> OpenSDKErrorDetails(
                code = "GATT_CONNECT_FAILED",
                numericCode = 2001,
                category = "BLE Access",
                messageEn = "BLE GATT connection to access control terminal failed",
                messageFa = "ارتباط بلوتوث با دستگاه اکسس کنترل برقرار نشد",
                recoveryStrategy = OpenSDKRecoveryStrategy.RETRY_BACKOFF,
                actionSuggestion = "Move closer to access control reader and restart scan."
            )
            else -> OpenSDKErrorDetails(
                code = errorCode,
                numericCode = null,
                category = "General",
                messageEn = "OpenSDK status code: $errorCode",
                messageFa = "کد وضعیت اس‌دی‌کی: $errorCode",
                recoveryStrategy = OpenSDKRecoveryStrategy.RETRY_BACKOFF,
                actionSuggestion = "Restart player window and check camera connectivity."
            )
        }
    }

    /**
     * Executes automatic recovery action given an error callback
     */
    fun handlePlayerError(
        errorCode: String,
        onRetry: () -> Unit,
        onReauth: () -> Unit,
        onFallbackSubstream: () -> Unit
    ) {
        val details = resolve(errorCode)
        Log.w(TAG, "Resolving OpenSDK Error [${details.code}]: ${details.messageEn}")
        when (details.recoveryStrategy) {
            OpenSDKRecoveryStrategy.RETRY_BACKOFF -> onRetry()
            OpenSDKRecoveryStrategy.REAUTHENTICATE -> onReauth()
            OpenSDKRecoveryStrategy.FALLBACK_SUBSTREAM -> onFallbackSubstream()
            else -> onRetry()
        }
    }
}
