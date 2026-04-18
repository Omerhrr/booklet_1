<script setup>
import { ref, nextTick, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import {
  getWizardSessions,
  createWizardSession,
  getWizardSession,
  addWizardMessage,
} from '@/api/agents'

const loading = ref(true)
const sessions = ref([])
const activeSessionId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const generating = ref(false)

const chatEndRef = ref(null)

function scrollToBottom() {
  nextTick(() => { chatEndRef.value?.scrollIntoView({ behavior: 'smooth' }) })
}

async function loadSessions() {
  try {
    const { data } = await getWizardSessions()
    sessions.value = Array.isArray(data) ? data : data.items || []
  } catch (error) {
    console.error('Failed to load wizard sessions:', error)
  }
}

async function selectSession(id) {
  activeSessionId.value = id
  loading.value = true
  try {
    const { data } = await getWizardSession(id)
    messages.value = Array.isArray(data) ? data : data.messages || []
  } catch (error) {
    console.error('Failed to load session:', error)
    messages.value = []
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function startNewSession() {
  try {
    const { data } = await createWizardSession({ type: 'document' })
    activeSessionId.value = data.id
    messages.value = data.messages || [{ role: 'assistant', content: 'Hello! I\'m your Document Wizard. Tell me what kind of document you need (e.g., invoice, contract, report) and I\'ll help you generate it.', created_at: new Date().toISOString() }]
    await loadSessions()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || sending.value) return
  if (!activeSessionId.value) { await startNewSession() }

  messages.value.push({ role: 'user', content: text, created_at: new Date().toISOString() })
  inputMessage.value = ''
  scrollToBottom()
  sending.value = true
  try {
    const { data } = await addWizardMessage(activeSessionId.value, { message: text })
    const assistantMsg = data.message || data.assistant_message || { role: 'assistant', content: data.response || '' }
    messages.value.push(typeof assistantMsg === 'string' ? { role: 'assistant', content: assistantMsg } : assistantMsg)
  } catch (error) {
    console.error('Failed to send message:', error)
    messages.value.push({ role: 'assistant', content: 'Sorry, an error occurred. Please try again.' })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  await loadSessions()
  loading.value = false
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Document Wizard</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Generate business documents with AI assistance</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors self-start"
        @click="startNewSession"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        New Session
      </button>
    </div>

    <!-- Session Selector -->
    <div v-if="sessions.length > 0" class="flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="session in sessions"
        :key="session.id"
        type="button"
        :class="[
          'flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full border transition-colors',
          activeSessionId === session.id
            ? 'bg-violet-100 text-violet-700 border-violet-300 dark:bg-violet-900/40 dark:text-violet-400 dark:border-violet-700'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700 dark:hover:bg-gray-700',
        ]"
        @click="selectSession(session.id)"
      >
        {{ session.title || session.name || `Session ${session.id}` }}
      </button>
    </div>

    <!-- Chat Interface -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <!-- Messages -->
      <div class="h-[500px] overflow-y-auto px-6 py-4 space-y-4">
        <div v-if="messages.length === 0 && !sending" class="flex flex-col items-center justify-center h-full">
          <div class="w-16 h-16 mb-4 rounded-full bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center">
            <svg class="w-8 h-8 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">Document Wizard</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 max-w-md text-center">Start a new session to generate invoices, contracts, reports, or other business documents.</p>
          <button type="button" class="mt-4 px-4 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors" @click="startNewSession">Start Session</button>
        </div>

        <template v-else>
          <div v-for="(msg, idx) in messages" :key="idx" :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
            <div :class="['max-w-[80%] rounded-2xl px-4 py-3', msg.role === 'user' ? 'bg-violet-600 text-white rounded-br-md' : 'bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-bl-md']">
              <div class="text-sm leading-relaxed whitespace-pre-wrap">{{ msg.content }}</div>
              <!-- Document Preview -->
              <div v-if="msg.document_url" class="mt-3 p-3 bg-white/10 dark:bg-black/20 rounded-lg">
                <p class="text-xs font-medium mb-2 opacity-80">Generated Document:</p>
                <a :href="msg.document_url" target="_blank" class="inline-flex items-center gap-1 text-xs font-medium underline">
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  Download Document
                </a>
              </div>
              <div :class="['text-xs mt-1', msg.role === 'user' ? 'text-violet-200' : 'text-gray-400 dark:text-gray-500']">{{ formatTime(msg.created_at) }}</div>
            </div>
          </div>

          <div v-if="sending" class="flex justify-start">
            <div class="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0ms" />
                <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 150ms" />
                <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 300ms" />
              </div>
            </div>
          </div>
        </template>

        <div ref="chatEndRef" />
      </div>

      <!-- Input -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-end gap-3">
          <textarea
            v-model="inputMessage"
            rows="1"
            placeholder="Describe the document you need..."
            class="flex-1 px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 resize-none transition-colors"
            @keydown="handleKeydown"
          />
          <button
            type="button"
            class="flex-shrink-0 w-11 h-11 flex items-center justify-center bg-violet-600 text-white rounded-xl hover:bg-violet-700 disabled:opacity-50 transition-colors"
            :disabled="!inputMessage.trim() || sending"
            @click="sendMessage"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
