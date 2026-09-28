<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'

const router = useRouter()

const name = ref('')
const address = ref('')
const city = ref('')
const country = ref('')
const error = ref('')
const submitting = ref(false)

async function submitProperty() {
  error.value = ''
  submitting.value = true
  try {
    const response = await api.post('properties/', {
      name: name.value,
      address: address.value,
      city: city.value,
      country: country.value,
    })
    router.push(`/properties/${response.data.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not create property.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
      Property Setup
    </p>
    <h2 class="font-display text-ivory text-3xl mb-8">Add a Property</h2>

    <form @submit.prevent="submitProperty" class="bg-panel border border-white/5 rounded-sm p-6 max-w-md flex flex-col gap-4">
      <div>
        <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Property name</label>
        <input v-model="name" required
               class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
      </div>
      <div>
        <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Address</label>
        <input v-model="address" required
               class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">City</label>
          <input v-model="city" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Country</label>
          <input v-model="country" required
                 class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory focus:outline-none focus:border-brass/60" />
        </div>
      </div>

      <p v-if="error" class="text-clay text-sm">{{ error }}</p>

      <button type="submit" :disabled="submitting"
              class="mt-2 bg-brass text-ink font-medium py-2.5 rounded-sm hover:bg-brass/90 disabled:opacity-50 transition-colors">
        {{ submitting ? 'Creating…' : 'Create property' }}
      </button>
    </form>
  </AppShell>
</template>