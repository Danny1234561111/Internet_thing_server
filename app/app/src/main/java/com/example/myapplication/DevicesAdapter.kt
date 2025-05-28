package com.example.myapplication
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class DevicesAdapter(private val onClick: (DeviceOut) -> Unit) : RecyclerView.Adapter<DevicesAdapter.DeviceViewHolder>() {

    private val devices = mutableListOf<DeviceOut>()

    fun submitList(newDevices: List<DeviceOut>) {
        devices.clear()
        devices.addAll(newDevices)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DeviceViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_device, parent, false)
        return DeviceViewHolder(view)
    }

    override fun onBindViewHolder(holder: DeviceViewHolder, position: Int) {
        val device = devices[position]
        holder.bind(device)
    }

    override fun getItemCount(): Int = devices.size

    inner class DeviceViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val nameTv: TextView = itemView.findViewById(R.id.deviceNameTextView)

        fun bind(device: DeviceOut) {
            nameTv.text = device.name
            itemView.setOnClickListener { onClick(device) }
        }
    }
}
