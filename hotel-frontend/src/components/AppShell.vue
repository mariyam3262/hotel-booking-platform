<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-ink font-body">
    <header class="border-b border-white/10 px-4 sm:px-8 py-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-4 sm:gap-8 flex-wrap">
        <h1 class="font-display text-ivory text-lg sm:text-xl">Meridian</h1>
        <nav class="flex gap-3 sm:gap-5 text-xs sm:text-sm">
          <router-link to="/" class="text-slate hover:text-ivory transition-colors">Properties</router-link>
          <router-link to="/dashboard" class="text-slate hover:text-ivory transition-colors">Dashboard</router-link>
          <router-link to="/concierge" class="text-slate hover:text-ivory transition-colors">Concierge</router-link>
        </nav>
      </div>
      <button @click="handleLogout" class="text-slate text-xs sm:text-sm hover:text-ivory transition-colors">
        Sign out
      </button>
    </header>
    <main class="px-4 sm:px-8 py-6 sm:py-10">
      <slot />
    </main>
  </div>
</template>