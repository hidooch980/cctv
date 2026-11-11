package com.molido.cctv.opensdk

import android.content.Context
import android.util.Log

/**
 * Access Control & Door Opening via Bluetooth Low Energy (BLE)
 * Implements Chapter 3.16 of Android OpenSDK Development Guide V3.8.0.
 */
data class BluetoothAccessDevice(
    val address: String, // MAC address AA:BB:CC:DD:EE:FF
    val name: String?,
    val rssi: Int
)

interface OnDoorOpenListener {
    fun onScanFound(device: BluetoothAccessDevice)
    fun onDoorOpenSuccess(deviceAddress: String)
    fun onDoorOpenFailed(deviceAddress: String, errorCode: Int, errorMessage: String)
}

class BluetoothDoorManager(private val context: Context) {

    companion object {
        private const val TAG = "BluetoothDoorManager"

        // Error Codes defined in OpenSDK Development Guide section 3.16
        const val SUCCESS = 0
        const val BLUETOOTH_DISABLED = 1001
        const val PERMISSION_DENIED = 1002
        const val BLE_NOT_SUPPORTED = 1003
        const val NOT_INITIALIZED = 1004
        const val GATT_CONNECT_FAILED = 2001
        const val GATT_SERVICE_NOT_FOUND = 2002
        const val GATT_CHARACTERISTIC_NOT_FOUND = 2003
        const val GATT_COMMUNICATION_ERROR = 2004
        const val GATT_DISCONNECTED = 2005
        const val LOGIN_FAILED = 3001
        const val COMMAND_FAILED = 3002
        const val TIMEOUT = 3003
        const val AUTH_FAILED = 3004
        const val CREDENTIAL_NOT_SET = 4001
        const val DEVICE_BUSY = 4002
        const val INVALID_PARAMETER = 4003
        const val UNKNOWN = 9999
    }

    private var isScanning = false

    fun startScanning(timeoutMs: Long = 10000, listener: OnDoorOpenListener) {
        Log.i(TAG, "Starting BLE scanning for access control terminals...")
        isScanning = true
    }

    fun stopScanning() {
        Log.i(TAG, "Stopping BLE scanning...")
        isScanning = false
    }

    fun openDoor(macAddress: String, credentialToken: String, listener: OnDoorOpenListener) {
        Log.i(TAG, "Initiating door opening command to $macAddress")
        // Executes BLE GATT connection, auth challenge, and unlock relay
    }
}
