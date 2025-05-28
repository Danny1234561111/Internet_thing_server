package com.example.myapplication

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.content.SharedPreferences
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {

    private lateinit var usernameEt: EditText
    private lateinit var passwordEt: EditText
    private lateinit var loginBtn: Button
    private lateinit var registerBtn: Button
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        usernameEt = findViewById(R.id.usernameEditText)
        passwordEt = findViewById(R.id.passwordEditText)
        loginBtn = findViewById(R.id.loginButton)
        registerBtn = findViewById(R.id.registerButton)

        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)

        // Создаем канал уведомлений
        createNotificationChannel()

        loginBtn.setOnClickListener {
            val username = usernameEt.text.toString()
            val password = passwordEt.text.toString()

            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Введите имя пользователя и пароль", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val api = RetrofitClient.apiService
            api.login(UserLogin(username, password)).enqueue(object : Callback<Token> {
                override fun onResponse(call: Call<Token>, response: Response<Token>) {
                    if (response.isSuccessful && response.body() != null) {
                        val token = response.body()!!.access_token
                        prefs.edit().putString("accessToken", token).putString("username", username).apply()

                        // Переход к следующему экрану, например DevicesActivity
                        startActivity(Intent(this@LoginActivity, DevicesActivity::class.java))
                        finish()
                    } else {
                        Toast.makeText(this@LoginActivity, "Ошибка входа: ${response.message()}", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onFailure(call: Call<Token>, t: Throwable) {
                    Toast.makeText(this@LoginActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        }

        registerBtn.setOnClickListener {
            // Переход на экран регистрации (можно реализовать аналогично)
            startActivity(Intent(this, RegistrationActivity::class.java))
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Device Changes"
            val descriptionText = "Channel for device changes notifications"
            val importance = NotificationManager.IMPORTANCE_DEFAULT
            val channel = NotificationChannel("YOUR_CHANNEL_ID", name, importance).apply {
                description = descriptionText
            }
            val notificationManager: NotificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
}
