
package com.example.myapplication

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
class MyService : LifecycleService() {
    private var notificationIdCounter = 1

    private lateinit var prefs: SharedPreferences
    private val CHANNEL_ID = "SecurityNotificationsChannel"
    private val SERVICE_DELAY = 60 * 1000L // 1 minute
    private val TAG = "MyService"

    override fun onCreate() {
        super.onCreate()
        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)
        createNotificationChannel()

        // Создайте уведомление для foreground
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)

        Log.d(TAG, "Service created and moved to foreground")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        Log.d(TAG, "Service started")
        startFetchingData()
        return START_REDELIVER_INTENT
    }

    private fun startFetchingData() {
        lifecycleScope.launch {
            while (true) {
                fetchData()
                delay(SERVICE_DELAY)
            }
        }
    }

    private fun fetchData() {
        val token = prefs.getString("accessToken", null)
        if (token == null) {
            Log.e(TAG, "Token is null, stopping service")
            stopSelf()
            return
        }
        RetrofitClient.apiService.getLogs("Bearer $token")
            .enqueue(object : Callback<List<LogsResponse>> {
                override fun onResponse(
                    call: Call<List<LogsResponse>>,
                    response: Response<List<LogsResponse>>
                ) {
                    if (response.isSuccessful) {
                        val logs = response.body()
                        logs?.let {
                            if (it.any { log -> log.eventType == "danger" }) {
                                Log.d(
                                    TAG,
                                    "Danger event detected, checking permission and showing notification"
                                )
                                showNotification()
                            } else {
                                val eventTypes = it.map { log -> log.eventType }.joinToString(", ")
                                Log.d(TAG, "No danger event detected. Event types: $eventTypes")
                            }
                        } ?: run {
                            Log.w(TAG, "Response body is null")
                        }
                    } else {
                        val errorMessage = response.message() ?: "Unknown error"
                        Log.e(TAG, "API Error: $errorMessage")
                    }
                }

                override fun onFailure(call: Call<List<LogsResponse>>, t: Throwable) {
                    Log.e(TAG, "Network Error: ${t.message}")
                }
            })
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channelName = "Несанкционированный доступ"
            val channelDescription = "Проверьте это точно были вы?"
            val importance = NotificationManager.IMPORTANCE_HIGH

            val channel = NotificationChannel(CHANNEL_ID, channelName, importance).apply {
                description = channelDescription
                enableLights(true)
                enableVibration(true)
            }

            val notificationManager: NotificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)

            Log.d(TAG, "Notification channel created: $CHANNEL_ID")
        }
    }

    private fun showNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ActivityCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                Log.w(TAG, "Нет разрешения POST_NOTIFICATIONS, пропускаем уведомление")
                return
            }
        }

        val intent = Intent(this, LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }

        val pendingIntentFlags = when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            else -> PendingIntent.FLAG_UPDATE_CURRENT
        }

        val pendingIntent = PendingIntent.getActivity(this, 0, intent, pendingIntentFlags)

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.call)
            .setContentTitle("Несанкционированный доступ")
            .setContentText("Вход без отключения сигнализации")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setDefaults(NotificationCompat.DEFAULT_ALL)

        with(NotificationManagerCompat.from(this)) {
            notify(notificationIdCounter++, builder.build())
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "Service destroyed")
    }

    companion object {
        const val NOTIFICATION_ID = 1
    }

    private fun createNotification(): Notification {
        val intent = Intent(this, LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }

        val pendingIntentFlags = when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            else -> PendingIntent.FLAG_UPDATE_CURRENT
        }

        val pendingIntent = PendingIntent.getActivity(this, 0, intent, pendingIntentFlags)

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.call)
            .setContentTitle("Работает сервис")
            .setContentText("Сервис запущен и работает в фоне")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .build()
    }
}