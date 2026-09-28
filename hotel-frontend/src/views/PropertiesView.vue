<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/axios'
import AppShell from '../components/AppShell.vue'
import SkeletonCard from '../components/SkeletonCard.vue'

const properties = ref([])
const error = ref('')
const loading = ref(true)
const router = useRouter()

onMounted(async () => {
  try {
    const response = await api.get('properties/')
    properties.value = response.data
  } catch (err) {
    error.value = 'Could not load properties.'
  } finally {
    loading.value = false
  }
})

function goToProperty(id) {
  router.push(`/properties/${id}`)
}
</script>

<template>
  <AppShell>
    <div class="flex items-center justify-between mb-8 gap-4 flex-wrap">
      <div>
        <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
          Your Properties
        </p>
        <h2 class="font-display text-ivory text-3xl">Portfolio Overview</h2>
      </div>
      <router-link
        to="/properties/new"
        class="bg-brass text-ink text-sm font-medium px-4 py-2.5 rounded-sm hover:bg-brass/90 transition-colors shrink-0"
      >
        + Add Property
      </router-link>
    </div>

    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <SkeletonCard v-for="i in 3" :key="i" />
    </div>
    <p v-else-if="error" class="text-clay">{{ error }}</p>
    <p v-else-if="properties.length === 0" class="text-slate">
      No properties assigned to your account yet.
    </p>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="(property, i) in properties" :key="property.id" v-motion :initial="{ opacity: 0, y: 16 }"
        :enter="{ opacity: 1, y: 0, transition: { duration: 400, delay: i * 60 } }" class="group bg-panel rounded-sm overflow-hidden border border-white/5
         hover:border-brass/40 hover:-translate-y-1 hover:shadow-xl hover:shadow-black/30
         transition-all duration-200">
        <div @click="goToProperty(property.id)" class="cursor-pointer">
          <div class="h-32 bg-gradient-to-br from-brass/20 via-panel to-ink flex items-center justify-center">
            <span class="font-display text-brass/50 text-4xl">
              {{ property.name.charAt(0) }}
            </span>
          </div>

          <div class="p-5">
            <h3 class="font-display text-ivory text-lg mb-1 group-hover:text-brass transition-colors">
              {{ property.name }}
            </h3>
            <p class="text-slate text-sm">{{ property.city }}, {{ property.country }}</p>

            <div class="flex items-center justify-between mt-4 pt-4 border-t border-white/5">
              <span class="font-mono text-slate/60 text-xs">
                {{ property.room_types?.length || 0 }} room types
              </span>
              <span class="text-brass text-sm group-hover:translate-x-1 transition-transform inline-block">
                View →
              </span>
            </div>
          </div>
        </div>

        <router-link :to="`/admin/properties/${property.id}/staff`" @click.stop
          class="block text-center text-xs text-slate hover:text-brass border-t border-white/5 py-2 transition-colors">
     
    Manage Property
  </router-link>
</div>
    </div>
  </AppShell>
</template>