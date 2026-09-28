<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const route = useRoute()
const propertyId = Number(route.params.id)
const memberships = ref([])
const loading = ref(true)
const error = ref('')

const newUsername = ref('')
const newRole = ref('front_desk')
const submitting = ref(false)
const submitError = ref('')

async function loadMemberships() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('memberships/')
    console.log('Raw memberships response:', response.data)
    memberships.value = response.data.filter((m) => Number(m.property) === propertyId)
  } catch (err) {
    console.error('Failed to load memberships:', err.response?.data || err.message)
    error.value = 'Could not load staff.'
  } finally {
    loading.value = false
  }
}

onMounted(loadMemberships)

async function addStaff() {
  submitError.value = ''
  submitting.value = true
  try {
    const response = await api.post('memberships/', {
      property: propertyId,
      user_username: newUsername.value,
      role: newRole.value,
    })
    console.log('Created membership:', response.data)
    newUsername.value = ''
    await loadMemberships()
  } catch (err) {
    console.error('Failed to add staff:', err.response?.status, err.response?.data)
    const data = err.response?.data
    submitError.value =
      (typeof data === 'string' && data) ||
      data?.non_field_errors?.[0] ||
      data?.detail ||
      JSON.stringify(data) ||
      'Could not add staff member.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
      Staff Access
    </p>
    <h2 class="font-display text-ivory text-3xl mb-8">Manage Team</h2>

    <div class="bg-panel border border-white/5 rounded-sm p-5 mb-8 max-w-lg">
      <h3 class="font-display text-ivory text-lg mb-4">Add Staff Member</h3>
      <form @submit.prevent="addStaff" class="flex flex-wrap gap-3 items-end">
        <div class="flex-1 min-w-[140px]">
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Username</label>
          <input v-model="newUsername" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div class="w-36">
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Role</label>
          <select v-model="newRole"
                  class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2 text-ivory focus:outline-none focus:border-brass/60">
            <option value="owner">Owner</option>
            <option value="manager">Manager</option>
            <option value="front_desk">Front Desk</option>
          </select>
        </div>
        <button type="submit" :disabled="submitting"
                class="bg-brass text-ink font-medium px-4 py-2 rounded-sm hover:bg-brass/90 disabled:opacity-50 transition-colors">
          {{ submitting ? 'Adding…' : 'Add' }}
        </button>
      </form>
      <p v-if="submitError" class="text-clay text-sm mt-2 break-words">{{ submitError }}</p>
    </div>

    <p v-if="loading" class="text-slate">Loading…</p>
    <p v-else-if="error" class="text-clay">{{ error }}</p>

    <div v-else class="bg-panel border border-white/5 rounded-sm overflow-hidden max-w-lg">
      <div
        v-for="member in memberships"
        :key="member.id"
        class="flex items-center justify-between px-5 py-3 border-b border-white/5 last:border-0"
      >
        <span class="text-ivory">{{ member.username }}</span>
        <span class="font-mono text-xs text-brass capitalize">{{ member.role.replace('_', ' ') }}</span>
      </div>
      <p v-if="memberships.length === 0" class="text-slate text-sm p-5">
        No staff added yet.
      </p>
    </div>
  </AppShell>
</template>