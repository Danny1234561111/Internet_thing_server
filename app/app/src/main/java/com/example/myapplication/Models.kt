package com.example.myapplication

import android.os.Parcelable
import com.google.gson.annotations.SerializedName
import java.io.Serializable

//import java.io.Serializable

// User.kt

data class UserOut(
    val id: Int,
    val username: String
)
data class UserCreate(val username: String, val password: String)
data class UserLogin(val username: String, val password: String)
data class Token(val access_token: String, val token_type: String)
data class DeviceUpdate(val unique_key: String)

data class DeviceOut(
    val id: Int,
    val name: String,
    val unique_key: String,
    val pin_code: String,
    val active: Boolean
) : Serializable
data class PinChecksRequest(val pin_code: String, val unique_key: String)



data class PinCheckResponse(val pin_valid: Boolean)
data class PinChangeRequest(val unique_key: String, val old_pin: String, val new_pin: String)
data class ChangePasswordRequest(val unique_key: String, val old_password: String, val new_password: String)
data class LogsRequest(val unique_key: String)
data class EventPost(val unique_key: String, val event_type: String)
data class LogsResponse(
    val timestamp: String,
    val id: Int,
    @SerializedName("device_id") // Используй это, если ключ JSON отличается
    val deviceId: Int,
    @SerializedName("event_type")
    val eventType: String,
    val info: String? // Сделай допускающим null, если значение может быть null
)
data class PinCheckEvent(
    val device_id: Int,
    val event_type: String,
    val info: String,
    val timestamp: String,
    val id: Int
)


