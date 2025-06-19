package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class RegistrationActivity : AppCompatActivity() {

    private lateinit var usernameEt: EditText
    private lateinit var passwordEt: EditText
    private lateinit var registerBtn: Button
    private lateinit var backBtn: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_registration)

        usernameEt = findViewById(R.id.usernameEditText)
        passwordEt = findViewById(R.id.passwordEditText)
        registerBtn = findViewById(R.id.registerButton)
        backBtn = findViewById(R.id.backButton)

        backBtn.setOnClickListener {
            val intent = Intent(this, LoginActivity::class.java)
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            startActivity(intent)
        }
        registerBtn.setOnClickListener {
            val username = usernameEt.text.toString().trim()
            val password = passwordEt.text.toString().trim()

            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Введите имя пользователя и пароль", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val api = RetrofitClient.apiService
            api.registerUser (UserCreate(username, password)).enqueue(object : Callback<UserOut> {
                override fun onResponse(call: Call<UserOut>, response: Response<UserOut>) {
                    if (response.isSuccessful) {
                        Toast.makeText(this@RegistrationActivity, "Регистрация успешна", Toast.LENGTH_SHORT).show()
                        startActivity(Intent(this@RegistrationActivity, LoginActivity::class.java))
                        finish()
                    } else {
                        Toast.makeText(this@RegistrationActivity, "Ошибка регистрации: ${response.message()}", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onFailure(call: Call<UserOut>, t: Throwable) {
                    Toast.makeText(this@RegistrationActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        }
    }
}
