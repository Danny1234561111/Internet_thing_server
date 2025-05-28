package com.example.myapplication

import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class AddDeviceActivity : AppCompatActivity() {

    private lateinit var deviceNameEditText: EditText
    private lateinit var deviceTypeEditText: EditText
    private lateinit var saveDeviceButton: Button
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_add_device)

        deviceNameEditText = findViewById(R.id.deviceNameEditText)
        saveDeviceButton = findViewById(R.id.saveDeviceButton)

        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)
        val token = prefs.getString("accessToken", null)

        if (token == null) {
            Toast.makeText(this, "Пожалуйста, войдите в систему", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        saveDeviceButton.setOnClickListener {
            val key = deviceNameEditText.text.toString()

            if (key.isEmpty()) {
                Toast.makeText(this, "Пожалуйста, заполните все поля", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val deviceUpdate = DeviceUpdate(unique_key = key)

            RetrofitClient.apiService.addDevice("Bearer $token", deviceUpdate)
                .enqueue(object : Callback<DeviceOut> {
                    override fun onResponse(call: Call<DeviceOut>, response: Response<DeviceOut>) {
                        if (response.isSuccessful) {
                            Toast.makeText(this@AddDeviceActivity, "Устройство добавлено", Toast.LENGTH_SHORT).show()
                            finish() // Закрываем экран и возвращаемся назад
                        } else {
                            Toast.makeText(this@AddDeviceActivity, "Ошибка: ${response.message()}", Toast.LENGTH_SHORT).show()
                        }
                    }

                    override fun onFailure(call: Call<DeviceOut>, t: Throwable) {
                        Toast.makeText(this@AddDeviceActivity, "Ошибка сети: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                })
        }
    }
}
