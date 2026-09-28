<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = 'Access denied — check your credentials and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-ink flex items-center justify-center relative overflow-hidden font-body">
    <!-- ambient spotlight, like light over a reception desk -->
    <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(198,161,91,0.08),_transparent_60%)]"></div>

    <div
      v-motion
      :initial="{ opacity: 0, y: 24 }"
      :enter="{ opacity: 1, y: 0, transition: { duration: 600, ease: 'easeOut' } }"
      class="relative w-full max-w-sm bg-panel rounded-sm px-9 py-10"
    >
      <!-- brass rule that draws in -->
      <div
        v-motion
        :initial="{ scaleX: 0 }"
        :enter="{ scaleX: 1, transition: { duration: 700, delay: 200, ease: 'easeOut' } }"
        class="absolute top-0 left-0 h-[2px] w-full bg-brass origin-left"
      ></div>

      <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-3">
        Staff Access
      </p>
      <h1 class="font-display text-ivory text-3xl mb-8">
        Sign in to Meridian
      </h1>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Username</label>
          <input
            v-model="username"
            type="text"
            class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory placeholder-slate/50
                   focus:outline-none focus:border-brass/60 transition-colors"
            placeholder="your.username"
          />
        </div>

        <div>
          <label class="block text-slate text-xs uppercase tracking-wide mb-1.5">Password</label>
          <input
            v-model="password"
            type="password"
            class="w-full bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory placeholder-slate/50
                   focus:outline-none focus:border-brass/60 transition-colors"
            placeholder="••••••••"
          />
        </div>

        <p v-if="error" class="text-clay text-sm">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="mt-2 bg-brass text-ink font-medium py-2.5 rounded-sm hover:bg-brass/90
                 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="font-mono text-slate/40 text-[10px] mt-8 tracking-wide">
        REF—{{ new Date().toISOString().slice(0, 10) }}
      </p>
    </div>
  </div>
</template>