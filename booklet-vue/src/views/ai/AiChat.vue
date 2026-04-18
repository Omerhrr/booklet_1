<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import {
  getConversations,
  createChat,
  getConversation,
  deleteConversation,
  archiveConversation,
} from '@/api/ai'

const loading = ref(true)
const conversations = ref([])
const activeConversationId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const showSidebar = ref(true)
const deleteDialog = ref({ show: false, id: null })

const chatEndRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (chatEndRef.value) {
      chatEndRef.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

async function loadConversations() {
  try {
    const { data } = await getConversations()
    conversations.value = Array.isArray(data) ? data : data.items || data.conversations || []
  } catch (error) {
    console.error('Failed to load conversations:', error)
  }
}

async function selectConversation(id) {
  activeConversationId.value = id
  loading.value = true
  try {
    const { data } = await getConversation(id)
    messages.value = Array.isArray(data) ? data : data.messages || data.items || []
  } catch (error) {
    console.error('Failed to load conversation:', error)
    messages.value = []
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function startNewConversation() {
  activeConversationId.value = null
  messages.value = []
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || sending.value) return

  if (!activeConversationId.value) {
    messages.value.push({ role: 'user', content: text, created_at: new Date().toISOString() })
    inputMessage.value = ''
    scrollToBottom()
    sending.value = true
    try {
      const { data } = await createChat({ message: text })
      activeConversationId.value = data.id || data.conversation_id
      const assistantMsg = data.message || data.assistant_message || { role: 'assistant', content: data.response || 'I processed your request.' }
      messages.value.push(typeof assistantMsg === 'string' ? { role: 'assistant', content: assistantMsg } : assistantMsg)
      await loadConversations()
    } catch (error) {
      console.error('Failed to send message:', error)
      messages.value.push({ role: 'assistant', content: 'Sorry, an error occurred. Please try again.' })
    } finally {
      sending.value = false
      scrollToBottom()
    }
    return
  }

  messages.value.push({ role: 'user', content: text, created_at: new Date().toISOString() })
  inputMessage.value = ''
  scrollToBottom()
  sending.value = true
  try {
    const { data } = await createChat({ conversation_id: activeConversationId.value, message: text })
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

async function handleDeleteConversation() {
  const id = deleteDialog.value.id
  if (!id) return
  try {
    await deleteConversation(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeConversationId.value === id) {
      startNewConversation()
    }
  } catch (error) {
    console.error('Failed to delete conversation:', error)
  }
}

async function archiveConversationHandler(id) {
  try {
    await archiveConversation(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeConversationId.value === id) {
      startNewConversation()
    }
  } catch (error) {
    console.error('Failed to archive conversation:', error)
  }
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatMarkdown(text) {
  if (!text) return ''
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>')
  escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 dark:bg-gray-800 p-3 rounded my-2 overflow-x-auto"><code>$1</code></pre>')
  escaped = escaped.replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1 rounded text-sm">$1</code>')
  escaped = escaped.replace(/\n/g, '<br>')
  return escaped
}

onMounted(async () => {
  await loadConversations()
  loading.value = false
})
</script>

<template>
  <div class="flex h-[calc(100vh-80px)] -m-6">
    <!-- Sidebar -->
    <aside
      :class="[
        'flex flex-col border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 transition-all duration-200',
        showSidebar ? 'w-72' : 'w-0 overflow-hidden',
      ]"
    >
      <!-- New Chat Button -->
      <div class="p-3 border-b border-gray-200 dark:border-gray-700">
        <button
          type="button"
          class="w-full inline-flex items-center justify-center gap-2 px-3 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
          @click="startNewConversation"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Chat
        </button>
      </div>

      <!-- Conversation List -->
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div v-if="conversations.length === 0" class="text-center py-8 text-xs text-gray-400 dark:text-gray-500">
          No conversations yet
        </div>
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="[
            'group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors',
            activeConversationId === conv.id
              ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
          ]"
          @click="selectConversation(conv.id)"
        >
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{{ conv.title || conv.name || 'Untitled' }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 truncate">{{ conv.last_message || '' }}</p>
          </div>
          <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-amber-500 dark:hover:text-amber-400 rounded transition-colors"
              title="Archive"
              @click.stop="archiveConversationHandler(conv.id)"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
              </svg>
            </button>
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 rounded transition-colors"
              title="Delete"
              @click.stop="deleteDialog = { show: true, id: conv.id }"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
      <!-- Chat Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            @click="showSidebar = !showSidebar"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ activeConversationId ? 'Continue Chat' : 'New Chat' }}
          </h2>
        </div>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        <div v-if="messages.length === 0 && !sending" class="flex flex-col items-center justify-center h-full">
          <div class="w-16 h-16 mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
            <svg class="w-8 h-8 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">AI Assistant</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 max-w-md text-center">Ask me anything about your business data, reports, or get help with your accounting tasks.</p>
        </div>

        <div v-for="(msg, idx) in messages" :key="idx" :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
          <div
            :class="[
              'max-w-[75%] rounded-2xl px-4 py-3',
              msg.role === 'user'
                ? 'bg-emerald-600 text-white rounded-br-md'
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-bl-md shadow-sm',
            ]"
          >
            <div class="text-sm leading-relaxed" v-html="msg.role === 'assistant' ? formatMarkdown(msg.content) : msg.content" />
            <div :class="['text-xs mt-1', msg.role === 'user' ? 'text-emerald-200' : 'text-gray-400 dark:text-gray-500']">
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>

        <!-- Typing Indicator -->
        <div v-if="sending" class="flex justify-start">
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
            <div class="flex items-center gap-1.5">
              <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0ms" />
              <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 150ms" />
              <div class="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style="animation-delay: 300ms" />
            </div>
          </div>
        </div>

        <div ref="chatEndRef" />
      </div>

      <!-- Input Area -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div class="flex items-end gap-3 max-w-4xl mx-auto">
          <div class="flex-1 relative">
            <textarea
              v-model="inputMessage"
              rows="1"
              placeholder="Type your message..."
              class="w-full px-4 py-3 pr-12 text-sm border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-none transition-colors"
              style="min-height: 44px; max-height: 120px;"
              @keydown="handleKeydown"
              @input="autoResize($event)"
            />
          </div>
          <button
            type="button"
            class="flex-shrink-0 w-11 h-11 flex items-center justify-center bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            :disabled="!inputMessage.trim() || sending"
            @click="sendMessage"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </div>
    </main>

    <!-- Delete Dialog -->
    <ConfirmDialog
      :show="deleteDialog.show"
      title="Delete Conversation"
      message="Are you sure you want to delete this conversation? This action cannot be undone."
      confirm-text="Delete"
      type="danger"
      @confirm="handleDeleteConversation"
      @update:show="deleteDialog.show = $event"
    />
  </div>
</template>
