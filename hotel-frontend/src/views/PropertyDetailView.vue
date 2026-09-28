<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const route = useRoute()
const router = useRouter()
const property = ref(null)
const loading = ref(true)
const error = ref('')

const checkIn = ref('')
const checkOut = ref('')
const selectedRoomType = ref(null)
const availableRooms = ref(null)
const searching = ref(false)
const searchError = ref('')

onMounted(async () => {
  try {
    const response = await api.get(`properties/${route.params.id}/`)
    property.value = response.data
  } catch (err) {
    error.value = 'Could not load this property.'
  } finally {
    loading.value = false
  }
})

async function searchAvailability(roomType) {
  if (!checkIn.value || !checkOut.value) {
    searchError.value = 'Select both check-in and check-out dates first.'
    return
  }
  searchError.value = ''
  searching.value = true
  selectedRoomType.value = roomType.id
  availableRooms.value = null

  try {
    const response = await api.get('availability', {
      params: {
        room_type: roomType.id,
        check_in: checkIn.value,
        check_out: checkOut.value,
      },
    })
    availableRooms.value = response.data
  } catch (err) {
    searchError.value = err.response?.data?.error || 'Search failed.'
  } finally {
    searching.value = false
  }
}
</script>

<template>
  <AppShell>
    <p v-if="loading" class="text-slate">Loading…</p>
    <p v-else-if="error" class="text-clay">{{ error }}</p>

    <div v-else-if="property">
      <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
        {{ property.city }}, {{ property.country }}
      </p>
      <h2 class="font-display text-ivory text-3xl mb-3">{{ property.name }}</h2>
      <p class="text-slate max-w-2xl mb-8">
        {{ property.ai_description || 'No description available yet.' }}
      </p>

      <div
        class="bg-panel border border-white/5 rounded-sm p-5 mb-8 flex flex-wrap items-end gap-4 shadow-lg shadow-black/20">
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Check-in</label>
          <input v-model="checkIn" type="date"
            class="bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Check-out</label>
          <input v-model="checkOut" type="date"
            class="bg-inpk border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <p v-if="searchError" class="text-clay text-sm">{{ searchError }}</p>
      </div>

      <h3 class="font-display text-ivory text-xl mb-4">Room Types</h3>

      <div class="flex flex-col gap-4">
        <div
          v-for="roomType in property.room_types"
          :key="roomType.id"
          class="bg-panel border border-white/5 rounded-sm p-5"
        >
          <div class="flex items-start justify-between gap-6">
            <div>
              <h4 class="font-display text-ivory text-lg">{{ roomType.name }}</h4>
              <p class="text-slate text-sm mt-1 max-w-md">{{ roomType.description || 'No description.' }}</p>
              <p class="font-mono text-brass text-sm mt-3">
                ${{ roomType.base_price_per_night }} / night · sleeps {{ roomType.max_occupancy }}
              </p>
            </div>
            <button
              @click="searchAvailability(roomType)"
              class="shrink-0 bg-brass text-ink text-sm font-medium px-4 py-2 rounded-sm hover:bg-brass/90 transition-colors"
            >
              Check availability
            </button>
          </div>

          <div v-if="selectedRoomType === roomType.id" class="mt-4 pt-4 border-t border-white/5">
            <p v-if="searching" class="text-slate text-sm">Searching…</p>
            <div v-else-if="availableRooms?.length" class="flex flex-wrap gap-2">
              <button
                v-for="room in availableRooms"
                :key="room.id"
                @click="router.push({
                  path: '/bookings/new',
                  query: {
                    room_id: room.id,
                    room_number: room.room_number,
                    check_in: checkIn,
                    check_out: checkOut,
                  },
                })"
                class="font-mono text-xs bg-ink border border-brass/30 text-brass px-3 py-1.5 rounded-sm hover:bg-brass hover:text-ink transition-colors"
              >
                Room {{ room.room_number }}
              </button>
            </div>
            <p v-else-if="availableRooms" class="text-slate text-sm">
              No rooms available for these dates.
            </p>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>