<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const route = useRoute()
const router = useRouter()

const roomId = route.query.room_id
const checkIn = route.query.check_in
const checkOut = route.query.check_out
const roomNumber = route.query.room_number

const guestName = ref('')
const guestEmail = ref('')
const guestPhone = ref('')
const totalPrice = ref('')
const submitting = ref(false)
const error = ref('')

async function submitBooking() {
  error.value = ''
  submitting.value = true
  try {
    const response = await api.post('bookings/', {
      room: roomId,
      check_in: checkIn,
      check_out: checkOut,
      total_price: totalPrice.value,
      guest: {
        full_name: guestName.value,
        email: guestEmail.value,
        phone: guestPhone.value,
      },
    })
    router.push(`/bookings/${response.data.id}`)
  } catch (err) {
    error.value = err.response?.data?.non_field_errors?.[0]
      || err.response?.data?.detail
      || 'Booking failed — please check the details and try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">New Booking</p>
    <h2 class="font-display text-ivory text-3xl mb-8">Room {{ roomNumber }}</h2>

    <div class="bg-panel border border-white/5 rounded-sm p-6 max-w-md">
      <div class="flex justify-between text-sm mb-6 pb-6 border-b border-white/5">
        <span class="text-slate">{{ checkIn }} → {{ checkOut }}</span>
      </div>

      <form @submit.prevent="submitBooking" class="flex flex-col gap-4">
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Guest name</label>
          <input v-model="guestName" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Email</label>
          <input v-model="guestEmail" type="email" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Phone</label>
          <input v-model="guestPhone"
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Total price ($)</label>
          <input v-model="totalPrice" type="number" step="0.01" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>

        <p v-if="error" class="text-clay text-sm">{{ error }}</p>

        <button type="submit" :disabled="submitting"
                class="mt-2 bg-brass text-ink font-medium py-2.5 rounded-sm hover:bg-brass/90 disabled:opacity-50 transition-colors">
          {{ submitting ? 'Booking…' : 'Confirm booking' }}
        </button>
      </form>
    </div>
  </AppShell>
</template>