<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'
import SkeletonCard from '../components/SkeletonCard.vue'

const bookings = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('all')

onMounted(async () => {
  try {
    const response = await api.get('bookings/')
    bookings.value = response.data
  } catch (err) {
    error.value = 'Could not load bookings.'
  } finally {
    loading.value = false
  }
})

const filteredBookings = computed(() => {
  if (statusFilter.value === 'all') return bookings.value
  return bookings.value.filter((b) => b.status === statusFilter.value)
})

const occupancyStats = computed(() => {
  const total = bookings.value.length
  const active = bookings.value.filter((b) =>
    ['pending', 'confirmed', 'checked_in'].includes(b.status)
  ).length
  const checkedIn = bookings.value.filter((b) => b.status === 'checked_in').length
  const cancelled = bookings.value.filter((b) => b.status === 'cancelled').length
  return { total, active, checkedIn, cancelled }
})

const statusStyles = {
  pending: 'bg-brass/10 text-brass border-brass/30',
  confirmed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  checked_in: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  checked_out: 'bg-slate/10 text-slate border-slate/30',
  cancelled: 'bg-clay/10 text-clay border-clay/30',
}
</script>

<template>
  <AppShell>
    <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
      Front Desk
    </p>
    <h2 class="font-display text-ivory text-3xl mb-8">Booking Dashboard</h2>

    <!-- loading skeletons -->
    <div v-if="loading" class="flex flex-col gap-6">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <SkeletonCard v-for="i in 4" :key="i" />
      </div>
      <div class="flex flex-col gap-3">
        <SkeletonCard v-for="i in 3" :key="i" />
      </div>
    </div>

    <p v-else-if="error" class="text-clay">{{ error }}</p>

    <template v-else>
      <!-- occupancy stat strip -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div class="bg-panel border border-white/5 rounded-sm p-4">
          <p class="font-mono text-2xl sm:text-3xl text-ivory">{{ occupancyStats.total }}</p>
          <p class="text-slate text-xs uppercase tracking-wide mt-1">Total Bookings</p>
        </div>
        <div class="bg-panel border border-white/5 rounded-sm p-4">
          <p class="font-mono text-2xl sm:text-3xl text-brass">{{ occupancyStats.active }}</p>
          <p class="text-slate text-xs uppercase tracking-wide mt-1">Active</p>
        </div>
        <div class="bg-panel border border-white/5 rounded-sm p-4">
          <p class="font-mono text-2xl sm:text-3xl text-blue-400">{{ occupancyStats.checkedIn }}</p>
          <p class="text-slate text-xs uppercase tracking-wide mt-1">Checked In</p>
        </div>
        <div class="bg-panel border border-white/5 rounded-sm p-4">
          <p class="font-mono text-2xl sm:text-3xl text-clay">{{ occupancyStats.cancelled }}</p>
          <p class="text-slate text-xs uppercase tracking-wide mt-1">Cancelled</p>
        </div>
      </div>

      <!-- status filter -->
      <div class="flex gap-2 mb-5 flex-wrap">
        <button
          v-for="status in ['all', 'pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']"
          :key="status"
          @click="statusFilter = status"
          class="text-xs px-3 py-1.5 rounded-sm border capitalize transition-colors"
          :class="statusFilter === status
            ? 'bg-brass text-ink border-brass'
            : 'bg-transparent text-slate border-white/10 hover:border-white/30'"
        >
          {{ status.replace('_', ' ') }}
        </button>
      </div>

      <!-- Desktop: table -->
      <div class="hidden md:block bg-panel border border-white/5 rounded-sm overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/5 text-left">
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Guest</th>
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Room</th>
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Check-in</th>
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Check-out</th>
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Total</th>
              <th class="px-5 py-3 text-slate font-medium text-xs uppercase tracking-wide">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="booking in filteredBookings"
              :key="booking.id"
              class="border-b border-white/5 last:border-0 hover:bg-white/[0.02]"
            >
              <td class="px-5 py-3 text-ivory">{{ booking.guest.full_name }}</td>
              <td class="px-5 py-3 text-slate">
                <span class="font-mono text-ivory">{{ booking.room_detail?.room_number }}</span>
                <span class="text-xs text-slate/60 ml-1">{{ booking.room_detail?.room_type_name }}</span>
              </td>
              <td class="px-5 py-3 text-slate font-mono">{{ booking.check_in }}</td>
              <td class="px-5 py-3 text-slate font-mono">{{ booking.check_out }}</td>
              <td class="px-5 py-3 text-brass font-mono">${{ booking.total_price }}</td>
              <td class="px-5 py-3">
                <span
                  class="text-xs px-2 py-1 rounded-sm border capitalize"
                  :class="statusStyles[booking.status]"
                >
                  {{ booking.status.replace('_', ' ') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <p v-if="filteredBookings.length === 0" class="text-slate text-sm p-5">
          No bookings match this filter.
        </p>
      </div>

      <!-- Mobile: stacked cards -->
      <div class="md:hidden flex flex-col gap-3">
        <div
          v-for="booking in filteredBookings"
          :key="booking.id"
          class="bg-panel border border-white/5 rounded-sm p-4"
        >
          <div class="flex items-center justify-between mb-2 gap-2">
            <span class="text-ivory font-medium truncate">{{ booking.guest.full_name }}</span>
            <span
              class="text-xs px-2 py-1 rounded-sm border capitalize shrink-0"
              :class="statusStyles[booking.status]"
            >
              {{ booking.status.replace('_', ' ') }}
            </span>
          </div>
          <div class="text-sm text-slate flex flex-col gap-1">
            <span class="font-mono text-ivory">
              {{ booking.room_detail?.room_number }} · {{ booking.room_detail?.room_type_name }}
            </span>
            <span>{{ booking.check_in }} → {{ booking.check_out }}</span>
            <span class="text-brass font-mono">${{ booking.total_price }}</span>
          </div>
        </div>

        <p v-if="filteredBookings.length === 0" class="text-slate text-sm">
          No bookings match this filter.
        </p>
      </div>
    </template>
  </AppShell>
</template>