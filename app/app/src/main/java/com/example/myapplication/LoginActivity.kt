
package com.example.myapplication

import android.Manifest
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.android.material.button.MaterialButton
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {

    private lateinit var prefs: SharedPreferences
    private lateinit var loginBtn: Button
    private lateinit var registerBtn: MaterialButton
    private lateinit var usernameEditText: EditText
    private lateinit var passwordEditText: EditText
    private val NOTIFICATION_PERMISSION_CODE = 123
    private val TAG = "LoginActivity"
    private var authToken: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)

        val currentVersion = BuildConfig.VERSION_NAME
        val savedVersion = prefs.getString("app_version", null)

        if (savedVersion != currentVersion) {
            prefs.edit().remove("accessToken").apply()
            prefs.edit().putString("app_version", currentVersion).apply()
        } else {
            val savedToken = prefs.getString("accessToken", null)
            if (!savedToken.isNullOrEmpty()) {
                authToken = savedToken
                // ЗАПРАШИВАЕМ РАЗРЕШЕНИЕ ПЕРЕД ЗАПУСКОМ АКТИВНОСТИ
                checkNotificationPermission()
                startActivity(Intent(this, DevicesActivity::class.java))
                finish()
                return
            }
        }

        loginBtn = findViewById(R.id.loginButton)
        registerBtn = findViewById(R.id.registerButton)
        usernameEditText = findViewById(R.id.usernameEditText)
        passwordEditText = findViewById(R.id.passwordEditText)

        registerBtn.setOnClickListener {
            val intent = Intent(this, RegistrationActivity::class.java)
            startActivity(intent)
        }

        loginBtn.setOnClickListener {
            val username = usernameEditText.text.toString()
            val password = passwordEditText.text.toString()
            performLogin(username, password)
        }
    }

    private fun performLogin(username: String, password: String) {
        val userLogin = UserLogin(username, password)
        RetrofitClient.apiService.login(userLogin).enqueue(object : Callback<Token> {
            override fun onResponse(call: Call<Token>, response: Response<Token>) {
                try {
                    if (response.isSuccessful && response.body() != null) {
                        authToken = response.body()!!.access_token
                        prefs.edit().putString("accessToken", authToken).apply()
                        prefs.edit().putString("username", username).apply()

                        Log.d(TAG, "Login successful, token: $authToken")

                        // ЗАПРАШИВАЕМ РАЗРЕШЕНИЕ ПЕРЕД ЗАПУСКОМ АКТИВНОСТИ
                        runOnUiThread {
                            checkNotificationPermission()
                            startActivity(Intent(this@LoginActivity, DevicesActivity::class.java))
                            finish()
                        }
                    } else {
                        val errorMessage = response.message() ?: "Unknown error"
                        Log.e(TAG, "Login failed: $errorMessage")
                        runOnUiThread {
                            Toast.makeText(this@LoginActivity, "Ошибка входа: $errorMessage", Toast.LENGTH_SHORT).show()
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Exception in onResponse: ${e.message}", e)
                    runOnUiThread {
                        Toast.makeText(this@LoginActivity, "Ошибка: ${e.message}", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<Token>, t: Throwable) {
                Log.e(TAG, "Network error: ${t.message}", t)
                runOnUiThread {
                    Toast.makeText(this@LoginActivity, "Ошибка сети: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            }
        })
    }

    private fun checkNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) == PackageManager.PERMISSION_DENIED
            ) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                    NOTIFICATION_PERMISSION_CODE
                )
            } else {
                Log.d(TAG, "Notification permission already granted")
                startMyService()// Запускаем сервис
            }
        } else {
            startMyService()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == NOTIFICATION_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Log.d(TAG, "Notification permission granted")
                startMyService() // Запускаем сервис только если разрешение получено
            } else {
                Log.w(TAG, "Notification permission denied")
                Toast.makeText(this, "Требуется разрешение на уведомления!", Toast.LENGTH_SHORT).show()
                // Можно показать объяснение, почему нужно разрешение
            }
        }
    }

    private fun startMyService() {
        if (authToken != null) {
            val serviceIntent = Intent(this, MyService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                // Для Android Oreo и выше используйте startForegroundService()
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
            Log.d(TAG, "Service started")
        } else {
            Log.e(TAG, "Cannot start service: Auth token is null")
            Toast.makeText(this, "Ошибка аутентификации!", Toast.LENGTH_SHORT).show()
        }
    }
}
