package com.example.myapplication

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
class DeviceDetailActivity : AppCompatActivity() {

    private lateinit var deviceNameTv: TextView
    private lateinit var deviceKeyTv: TextView
    private lateinit var devicePinTv: TextView
    private lateinit var changePinBtn: Button
    private lateinit var disarmBtn: Button
    private lateinit var eventsRecyclerView: RecyclerView
    private lateinit var eventsAdapter: PinCheckEventsAdapter
    private lateinit var prefs: SharedPreferences

    private var device: DeviceOut? = null
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_device_detail)

        deviceNameTv = findViewById(R.id.deviceNameTextView)
        deviceKeyTv = findViewById(R.id.deviceKeyTextView)
        devicePinTv = findViewById(R.id.devicePinTextView)
        changePinBtn = findViewById(R.id.changePinButton)
        disarmBtn = findViewById(R.id.disarmButton)
        eventsRecyclerView = findViewById(R.id.pinCheckEventsRecyclerView)

        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)
        token = prefs.getString("accessToken", null)

        device = intent.getSerializableExtra("device") as? DeviceOut

        updateDeviceDetails() // Обновляем детали устройства при создании активности

        eventsAdapter = PinCheckEventsAdapter()
        eventsRecyclerView.layoutManager = LinearLayoutManager(this)
        eventsRecyclerView.adapter = eventsAdapter

        // Загрузка событий при создании активности
        device?.unique_key?.let {
            loadPinCheckEvents(it)
        }

        changePinBtn.setOnClickListener {
            val intent = Intent(this, ChangePinActivity::class.java)
            intent.putExtra("device_unique_key", device?.unique_key)
            startActivity(intent)
        }

        disarmBtn.setOnClickListener {
            if (token == null || device?.unique_key == null) {
                Toast.makeText(this, "Ошибка: отсутствует токен или уникальный ключ", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            disarmDevice(token!!, device!!.unique_key)
        }
    }

    override fun onResume() {
        super.onResume()
        // Обновляем детали устройства и события при возвращении на страницу
        updateDeviceDetails()
        device?.unique_key?.let {
            loadPinCheckEvents(it)
        }
    }

    private fun updateDeviceDetails() {
        deviceNameTv.text = device?.name ?: "Device Name Not Available"
        deviceKeyTv.text = "Unique Key: ${device?.unique_key ?: "Not Available"}"
        devicePinTv.text = "PIN Code: ${device?.pin_code ?: "Not Available"}"
    }

    private fun loadPinCheckEvents(uniqueKey: String) {
        RetrofitClient.apiService.getPinChecks(uniqueKey).enqueue(object : Callback<List<PinCheckEvent>> {
            override fun onResponse(call: Call<List<PinCheckEvent>>, response: Response<List<PinCheckEvent>>) {
                if (response.isSuccessful) {
                    val events = response.body()
                    if (events != null) {
                        eventsAdapter.submitList(events)
                    } else {
                        Toast.makeText(this@DeviceDetailActivity, "События не найдены", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this@DeviceDetailActivity, "Ошибка загрузки событий: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<List<PinCheckEvent>>, t: Throwable) {
                Toast.makeText(this@DeviceDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun disarmDevice(token: String, uniqueKey: String) {
        val request = LogsRequest(unique_key = uniqueKey)
        RetrofitClient.apiService.disarmDevice("Bearer $token", request).enqueue(object : Callback<PinCheckResponse> {
            override fun onResponse(call: Call<PinCheckResponse>, response: Response<PinCheckResponse>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@DeviceDetailActivity, "Сигнализация отключена", Toast.LENGTH_SHORT).show()
                    // Обновить список событий после отключения
                    loadPinCheckEvents(uniqueKey)
                } else {
                    Toast.makeText(this@DeviceDetailActivity, "Ошибка отключения: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<PinCheckResponse>, t: Throwable) {
                Toast.makeText(this@DeviceDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }
}
