package com.example.myapplication

import android.graphics.Color
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

class PinCheckEventsAdapter : RecyclerView.Adapter<PinCheckEventsAdapter.ViewHolder>() {

    private var events: MutableList<PinCheckEvent> = mutableListOf()  // Use MutableList

    // Add a default empty list to avoid null exceptions

    fun submitList(newEvents: List<PinCheckEvent>) {
        Log.d("PinCheckEventsAdapter", "submitList called with ${newEvents.size} events")
        events.clear()
        events.addAll(newEvents.reversed()) // Add the reversed list
        notifyDataSetChanged()
        Log.d("PinCheckEventsAdapter", "Events size after submitList: ${events.size}")
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_pin_check_event, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        Log.d("PinCheckEventsAdapter", "Binding event at position: $position")
        val event = events[position]
        holder.bind(event)
    }

    override fun getItemCount(): Int {
        Log.d("PinCheckEventsAdapter", "getItemCount: ${events.size}")
        return events.size
    }

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val eventTextView: TextView = itemView.findViewById(R.id.eventTextView)
        private val timestampTextView: TextView = itemView.findViewById(R.id.timestampTextView)

        fun bind(event: PinCheckEvent) {
            Log.d("PinCheckEventsAdapter", "Binding data: ${event.event_type}, ${event.timestamp}")
            if (event.event_type=="pin_check"){
                eventTextView.text = "Успешный вход"
            }
            else{
                eventTextView.text = "Несанкционированный доступ"
            }
            val timestampString = event.timestamp

            try {
                // 1. Parse the timestamp string into a Date object
                val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS", Locale.getDefault()) // Adjust format if needed
                inputFormat.timeZone = TimeZone.getTimeZone("UTC") //  or your timezone
                val date = inputFormat.parse(timestampString)

                // 2. Format the Date object into a more readable string
                if (date != null) {
                    val outputFormat = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault()) // Customize the output format
                    outputFormat.timeZone = TimeZone.getDefault() // use the current timezone
                    val formattedTimestamp = outputFormat.format(date)
                    timestampTextView.text = formattedTimestamp
                } else {
                    timestampTextView.text = "Invalid Date" // Or handle the error appropriately
                }
            } catch (e: Exception) {
                // Handle parsing errors (e.g., invalid timestamp format)
                Log.e("PinCheckEventsAdapter", "Error parsing timestamp: ${e.message}")
                timestampTextView.text = "Invalid Date" // Display an error message
            }

            // Устанавливаем цвет текста в зависимости от типа события
            eventTextView.setTextColor(
                when (event.event_type) {
                    "danger" -> Color.RED
                    "pin_check" -> Color.BLUE
                    else -> Color.BLACK
                }
            )
        }
    }
}