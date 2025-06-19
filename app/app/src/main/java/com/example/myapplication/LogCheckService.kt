package com.example.myapplication
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.SharedPreferences
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response


class LogCheckService : Service() {

    private lateinit var handler: Handler
    private lateinit var prefs: SharedPreferences

    override fun onCreate() {
        super.onCreate()
        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)
        handler = Handler()
        createNotificationChannel()
        startLogCheck()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                "YOUR_CHANNEL_ID",
                "Log Notifications",
                NotificationManager.IMPORTANCE_HIGH
            )
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun startLogCheck() {
        handler.postDelayed(object : Runnable {
            override fun run() {
                checkLogs()
                handler.postDelayed(this, 60000) // Проверка каждые 60 секунд
            }
        }, 60000)
    }

    private fun checkLogs() {
        val token = prefs.getString("accessToken", null)
        if (token.isNullOrEmpty()) {
            Log.e("LogCheckService", "Token is null or empty")
            return
        }
        // Здесь должен быть ваш код для создания запроса на получение логов
        RetrofitClient.apiService.getLogs("$token").enqueue(object : Callback<List<LogsResponse>> {
            override fun onResponse(call: Call<List<LogsResponse>>, response: Response<List<LogsResponse>>) {
                if (response.isSuccessful) {
                    response.body()?.let { logs ->
                        for (log in logs) {
                            if (log.eventType == "danger") {
                                sendNotification("Внимание!", "Обнаружена попытка взлома!")
                                break
                            }
                        }
                    }
                } else {
                    Log.e("LogCheckService", "Ошибка получения логов: ${response.message()}")
                }
            }

            override fun onFailure(call: Call<List<LogsResponse>>, t: Throwable) {
                Log.e("LogCheckService", "Ошибка: ${t.message}")
            }
        })
    }

    private fun sendNotification(title: String, message: String) {
        val notificationManager = getSystemService(NotificationManager::class.java)
        val intent = Intent(this, LoginActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT)

        val notification = NotificationCompat.Builder(this, "YOUR_CHANNEL_ID")
            .setSmallIcon(R.drawable.call)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(1, notification)
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacksAndMessages(null) // Остановка проверок при уничтожении сервиса
    }
}
