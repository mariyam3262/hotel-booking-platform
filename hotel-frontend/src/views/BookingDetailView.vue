<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const route = useRoute()
const booking = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await api.get(`bookings/${route.params.id}/`)
    booking.value = response.data
  } catch (err) {
    error.value = 'Could not load this booking.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppShell>
    <p v-if="loading" class="text-slate">Loading…</p>
    <p v-else-if="error" class="text-clay">{{ error }}</p>

    <div v-else-if="booking" class="max-w-md">
      <div
        v-motion
        :initial="{ opacity: 0, y: 16 }"
        :enter="{ opacity: 1, y: 0, transition: { duration: 400 } }"
        class="bg-panel border border-brass/30 rounded-sm p-6"
      >
        <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
          Booking Confirmed
        </p>
        <h2 class="font-display text-ivory text-2xl mb-6">{{ booking.guest.full_name }}</h2>

        <div class="flex flex-col gap-3 text-sm">
          <div class="flex justify-between">
            <span class="text-slate">Check-in</span>
            <span class="text-ivory font-mono">{{ booking.check_in }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate">Check-out</span>
            <span class="text-ivory font-mono">{{ booking.check_out }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate">Total</span>
            <span class="text-brass font-mono">${{ booking.total_price }}</span>
          </div>
          <div class="flex justify-between pt-3 border-t border-white/5">
            <span class="text-slate">Status</span>
            <span class="text-ivory capitalize">{{ booking.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>