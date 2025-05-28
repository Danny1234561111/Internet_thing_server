package com.example.myapplication

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class DevicesActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: DevicesAdapter
    private lateinit var addDeviceBtn: Button
    private lateinit var prefs: SharedPreferences
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_devices)

        recyclerView = findViewById(R.id.devicesRecyclerView)
        addDeviceBtn = findViewById(R.id.addDeviceButton)
        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = DevicesAdapter { device -> onDeviceClicked(device) }
        recyclerView.adapter = adapter

        prefs = getSharedPreferences("MyAppPrefs", MODE_PRIVATE)
        token = prefs.getString("accessToken", null)

        if (token == null) {
            Toast.makeText(this, "Пожалуйста, войдите в систему", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        loadDevices(token!!)

        addDeviceBtn.setOnClickListener {
            val intent = Intent(this, AddDeviceActivity::class.java)
            startActivity(intent)
        }
    }

    override fun onResume() {
        super.onResume()
        // Обновляем список устройств при возвращении в активность
        token?.let { loadDevices(it) }
    }

    private fun loadDevices(token: String) {
        RetrofitClient.apiService.getDevices("Bearer $token").enqueue(object : Callback<List<DeviceOut>> {
            override fun onResponse(call: Call<List<DeviceOut>>, response: Response<List<DeviceOut>>) {
                if (response.isSuccessful) {
                    val devicesList = response.body()
                    if (devicesList != null) {
                        adapter.submitList(devicesList)
                    } else {
                        Toast.makeText(this@DevicesActivity, "Ошибка: список устройств пуст", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this@DevicesActivity, "Ошибка загрузки устройств: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<List<DeviceOut>>, t: Throwable) {
                Toast.makeText(this@DevicesActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun onDeviceClicked(device: DeviceOut) {
        val intent = Intent(this, DeviceDetailActivity::class.java)
        intent.putExtra("device", device)
        startActivity(intent)
    }
}
