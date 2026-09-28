<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const route = useRoute()
const property = ref(null)
const loading = ref(true)
const error = ref('')

// new room type form
const rtName = ref('')
const rtDescription = ref('')
const rtPrice = ref('')
const rtOccupancy = ref(2)
const rtSubmitting = ref(false)
const rtError = ref('')

// new room form (per room type)
const newRoomNumber = ref({})
const roomSubmitting = ref({})

async function loadProperty() {
  loading.value = true
  try {
    const response = await api.get(`properties/${route.params.id}/`)
    property.value = response.data
  } catch (err) {
    error.value = 'Could not load this property.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProperty)

async function addRoomType() {
  rtError.value = ''
  rtSubmitting.value = true
  try {
    await api.post('room-types/', {
      property: route.params.id,
      name: rtName.value,
      description: rtDescription.value,
      base_price_per_night: rtPrice.value,
      max_occupancy: rtOccupancy.value,
    })
    rtName.value = ''
    rtDescription.value = ''
    rtPrice.value = ''
    rtOccupancy.value = 2
    await loadProperty()
  } catch (err) {
    rtError.value = err.response?.data?.detail || 'Could not add room type.'
  } finally {
    rtSubmitting.value = false
  }
}

async function addRoom(roomTypeId) {
  const roomNumber = newRoomNumber.value[roomTypeId]
  if (!roomNumber) return
  roomSubmitting.value = { ...roomSubmitting.value, [roomTypeId]: true }
  try {
    await api.post('rooms/', { room_type: roomTypeId, room_number: roomNumber })
    newRoomNumber.value = { ...newRoomNumber.value, [roomTypeId]: '' }
    await loadProperty()
  } catch (err) {
    // simple inline handling — room number likely already exists for this type
  } finally {
    roomSubmitting.value = { ...roomSubmitting.value, [roomTypeId]: false }
  }
}
</script>

<template>
  <AppShell>
    <p v-if="loading" class="text-slate">Loading…</p>
    <p v-else-if="error" class="text-clay">{{ error }}</p>

    <div v-else-if="property">
      <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
        Managing
      </p>
      <h2 class="font-display text-ivory text-3xl mb-8">{{ property.name }}</h2>
      <router-link :to="`/admin/properties/${property.id}/staff`"
                class="text-brass text-sm hover:text-brass/80 transition-colors">
        Manage Staff →
    </router-link>

      <!-- add room type -->
      <div class="bg-panel border border-white/5 rounded-sm p-5 mb-8">
        <h3 class="font-display text-ivory text-lg mb-4">Add Room Type</h3>
        <form @submit.prevent="addRoomType" class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-[140px]">
            <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Name</label>
            <input v-model="rtName" required
                   class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
          </div>
          <div class="flex-[2] min-w-[200px]">
            <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Description</label>
            <input v-model="rtDescription"
                   class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
          </div>
          <div class="w-28">
            <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Price/night</label>
            <input v-model="rtPrice" type="number" step="0.01" required
                   class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
          </div>
          <div class="w-24">
            <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Sleeps</label>
            <input v-model="rtOccupancy" type="number" min="1" required
                   class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
          </div>
          <button type="submit" :disabled="rtSubmitting"
                  class="bg-brass text-ink font-medium px-4 py-2 rounded-sm hover:bg-brass/90 disabled:opacity-50 transition-colors">
            Add
          </button>
        </form>
        <p v-if="rtError" class="text-clay text-sm mt-2">{{ rtError }}</p>
      </div>

      <!-- room types + their rooms -->
      <h3 class="font-display text-ivory text-xl mb-4">Room Types</h3>
      <div class="flex flex-col gap-4">
        <div v-for="roomType in property.room_types" :key="roomType.id"
             class="bg-panel border border-white/5 rounded-sm p-5">
          <div class="flex items-start justify-between mb-4">
            <div>
              <h4 class="font-display text-ivory text-lg">{{ roomType.name }}</h4>
              <p class="font-mono text-brass text-sm mt-1">
                ${{ roomType.base_price_per_night }} / night · sleeps {{ roomType.max_occupancy }}
              </p>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 mb-3">
            <span v-for="room in roomType.rooms" :key="room.id"
                  class="font-mono text-xs bg-ink border border-white/10 text-ivory px-3 py-1.5 rounded-sm">
              {{ room.room_number }}
            </span>
            <span v-if="!roomType.rooms?.length" class="text-slate text-sm">No rooms yet.</span>
          </div>

          <form @submit.prevent="addRoom(roomType.id)" class="flex gap-2 max-w-xs">
            <input
              v-model="newRoomNumber[roomType.id]"
              placeholder="Room number (e.g. 101)"
              class="flex-1 min-w-0 bg-ink border border-white/10 rounded-sm px-3 py-2 text-sm text-ivory focus:outline-none focus:border-brass/60"
            />
            <button type="submit" :disabled="roomSubmitting[roomType.id]"
                    class="bg-ink border border-brass/30 text-brass text-sm px-3 py-2 rounded-sm hover:bg-brass hover:text-ink transition-colors shrink-0">
              + Add Room
            </button>
          </form>
        </div>

        <p v-if="!property.room_types?.length" class="text-slate text-sm">
          No room types yet — add one above.
        </p>
      </div>
    </div>
  </AppShell>
</template>