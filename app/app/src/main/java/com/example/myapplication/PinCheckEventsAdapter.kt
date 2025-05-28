package com.example.myapplication

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class PinCheckEventsAdapter : RecyclerView.Adapter<PinCheckEventsAdapter.EventViewHolder>() {

    private var eventsList: List<PinCheckEvent> = emptyList()

    fun submitList(list: List<PinCheckEvent>) {
        eventsList = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): EventViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_pin_check_event, parent, false)
        return EventViewHolder(view)
    }

    override fun onBindViewHolder(holder: EventViewHolder, position: Int) {
        val event = eventsList[position]
        holder.bind(event)
    }

    override fun getItemCount(): Int = eventsList.size

    class EventViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val infoTv: TextView = itemView.findViewById(R.id.infoTextView)
        private val timestampTv: TextView = itemView.findViewById(R.id.timestampTextView)

        fun bind(event: PinCheckEvent) {
            infoTv.text = event.info
            timestampTv.text = event.timestamp
        }
    }
}
