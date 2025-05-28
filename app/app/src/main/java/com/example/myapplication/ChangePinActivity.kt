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

class ChangePinActivity : AppCompatActivity() {

    private lateinit var oldPinEt: EditText
    private lateinit var newPinEt: EditText
    private lateinit var changePinBtn: Button
    private lateinit var prefs: SharedPreferences

    private var deviceUniqueKey: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_change_pin)

        // Инициализация элементов интерфейса
        oldPinEt = findViewById(R.id.oldPinEditText)
        newPinEt = findViewById(R.id.newPinEditText)
        changePinBtn = findViewById(R.id.changePinConfirmButton)

        // Получение SharedPreferences
        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)

        // Получение уникального ключа устройства
        deviceUniqueKey = intent.getStringExtra("device_unique_key")

        // Установка обработчика нажатия на кнопку
        changePinBtn.setOnClickListener {
            changePin()
        }
    }

    private fun changePin() {
        val oldPin = oldPinEt.text.toString().trim()
        val newPin = newPinEt.text.toString().trim()

        if (oldPin.isEmpty() || newPin.isEmpty()) {
            Toast.makeText(this, "Введите старый и новый PIN", Toast.LENGTH_SHORT).show()
            return
        }

        if (deviceUniqueKey == null) {
            Toast.makeText(this, "Ошибка: отсутствует уникальный ключ", Toast.LENGTH_SHORT).show()
            return
        }

        val token = prefs.getString("accessToken", null)
        if (token.isNullOrEmpty()) {
            Toast.makeText(this, "Ошибка: отсутствует токен авторизации", Toast.LENGTH_SHORT).show()
            return
        }

        val request = PinChangeRequest(
            unique_key = deviceUniqueKey!!,
            old_pin = oldPin,
            new_pin = newPin
        )

        RetrofitClient.apiService.changePin("Bearer $token", request)
            .enqueue(object : Callback<PinCheckResponse> {
                override fun onResponse(call: Call<PinCheckResponse>, response: Response<PinCheckResponse>) {
                    if (response.isSuccessful) {
                        val responseBody = response.body()
                            Toast.makeText(this@ChangePinActivity, "PIN успешно изменён", Toast.LENGTH_SHORT).show()
                            finish()
                    } else {
                        val errorMessage = response.errorBody()?.string() ?: "Неизвестная ошибка"
                        Toast.makeText(this@ChangePinActivity, "Ошибка изменения PIN: $errorMessage", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onFailure(call: Call<PinCheckResponse>, t: Throwable) {
                    Toast.makeText(this@ChangePinActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
    }

}