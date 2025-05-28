package com.example.myapplication

import retrofit2.Call
import retrofit2.http.*

interface ApiService {

    @POST("users/")
    fun registerUser(@Body userCreate: UserCreate): Call<UserOut>

    @POST("token")
    fun login(@Body userLogin: UserLogin): Call<Token>

    @POST("devices/")
    fun addDevice(
        @Header("Authorization") token: String,
        @Body deviceUpdate: DeviceUpdate
    ): Call<DeviceOut>

    @GET("devices/")
    fun getDevices(@Header("Authorization") token: String): Call<List<DeviceOut>>

    @POST("devices/check_pin")
    fun checkPin(@Body pinCheckRequest: PinChecksRequest): Call<PinCheckResponse>

    @POST("devices/change_pin")
    fun changePin(
        @Header("Authorization") token: String,
        @Body pinChangeRequest: PinChangeRequest
    ): Call<PinCheckResponse>


    @POST("devices/change_password")
    fun changePassword(
        @Header("Authorization") token: String,
        @Body changePasswordRequest: ChangePasswordRequest
    ): Call<Map<String, String>>

    @GET("devices/{unique_key}/pin_checks/")
    fun getPinChecks(
        @Path("unique_key") uniqueKey: String,
    ): Call<List<PinCheckEvent>>

    @POST("devices/disarm")
    fun disarmDevice(
        @Header("Authorization") token: String,
        @Body logsRequest: LogsRequest
    ): Call<PinCheckResponse>

    @POST("events/")
    fun postEvent(@Body eventPost: EventPost): Call<Map<String, String>>

    @POST("logs/")
    fun getLogs(
        @Header("Authorization") token: String,
        @Body logsRequest: LogsRequest
    ): Call<List<LogsResponse>>
}