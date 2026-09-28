<script setup>
import { ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppShell from '../components/AppShell.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const route = useRoute()
const auth = useAuthStore()

const propertyId = route.query.property_id || 1
const question = ref('')
const messages = ref([])
const asking = ref(false)
const chatEndRef = ref(null)

async function scrollToBottom() {
  await nextTick()
  chatEndRef.value?.scrollIntoView({ behavior: 'smooth' })
}

async function askConcierge() {
  if (!question.value.trim() || asking.value) return

  const userQuestion = question.value
  messages.value.push({ role: 'user', text: userQuestion })
  question.value = ''
  asking.value = true

  const assistantMessage = { role: 'assistant', text: '', sources: null }
  messages.value.push(assistantMessage)
  scrollToBottom()

  try {
    const response = await fetch('http://localhost:8000/api/v1/concierge/ask/stream/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question: userQuestion, property_id: propertyId }),
    })

    if (response.status === 401) {
      auth.logout()
      router.push('/login')
      return
    }

    if (!response.ok) {
      assistantMessage.text = 'The concierge is temporarily unavailable — please try again.'
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const event = JSON.parse(line.slice(6))

        if (event.type === 'sources') {
          assistantMessage.sources = event
        } else if (event.type === 'answer_chunk') {
          assistantMessage.text += event.text
          scrollToBottom()
        }
      }
    }
  } catch (err) {
    assistantMessage.text = 'Something went wrong reaching the concierge.'
  } finally {
    asking.value = false
  }
}

</script>


<template>
  <AppShell>
    <p class="text-brass text-[11px] tracking-[0.2em] uppercase font-medium mb-2">
      AI Concierge
    </p>
    <h2 class="font-display text-ivory text-2xl sm:text-3xl mb-4 sm:mb-6">Ask about this property</h2>

    <div class="bg-panel border border-white/5 rounded-sm flex flex-col h-[70vh] sm:h-[60vh] max-w-2xl">
      <!-- messages -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-5 flex flex-col gap-4 min-h-0">
        <p v-if="messages.length === 0" class="text-slate text-sm">
          Ask something like "what room options do you have" or "is it quiet at night."
        </p>

        <div
          v-for="(msg, i) in messages"
          :key="i"
          v-motion
          :initial="{ opacity: 0, y: 8 }"
          :enter="{ opacity: 1, y: 0, transition: { duration: 250 } }"
          class="max-w-[90%] sm:max-w-[85%]"
          :class="msg.role === 'user' ? 'self-end' : 'self-start'"
        >
          <div
            class="rounded-sm px-3.5 sm:px-4 py-2 sm:py-2.5 text-sm"
            :class="msg.role === 'user'
              ? 'bg-brass text-ink'
              : 'bg-ink border border-white/10 text-ivory'"
          >
            {{ msg.text || '…' }}
          </div>

          <div v-if="msg.sources?.reviews_used?.length" class="mt-1.5 flex gap-1.5 flex-wrap">
            <span
              v-for="r in msg.sources.reviews_used"
              :key="r.id"
              class="font-mono text-[10px] text-slate/60 bg-white/5 px-2 py-0.5 rounded-sm"
            >
              review #{{ r.id }} · {{ r.rating }}★
            </span>
          </div>
        </div>
        <div ref="chatEndRef"></div>
      </div>

      <!-- input -->
      <form @submit.prevent="askConcierge" class="border-t border-white/5 p-3 sm:p-4 flex gap-2 sm:gap-3 shrink-0">
        <input
          v-model="question"
          type="text"
          placeholder="Ask the concierge…"
          :disabled="asking"
          class="flex-1 min-w-0 bg-ink border border-white/10 rounded-sm px-3 py-2.5 text-ivory placeholder-slate/50
                 focus:outline-none focus:border-brass/60 disabled:opacity-50"
        />
        <button
          type="submit"
          :disabled="asking"
          class="bg-brass text-ink font-medium px-4 sm:px-5 py-2.5 rounded-sm hover:bg-brass/90 disabled:opacity-50 transition-colors shrink-0"
        >
          {{ asking ? '…' : 'Ask' }}
        </button>
      </form>
    </div>
  </AppShell>
</template>