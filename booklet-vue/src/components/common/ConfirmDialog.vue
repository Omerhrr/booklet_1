<script setup>
import Modal from './Modal.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Are you sure?',
  },
  message: {
    type: String,
    default: 'This action cannot be undone.',
  },
  confirmText: {
    type: String,
    default: 'Confirm',
  },
  cancelText: {
    type: String,
    default: 'Cancel',
  },
  type: {
    type: String,
    default: 'info',
    validator: (v) => ['danger', 'warning', 'info'].includes(v),
  },
  icon: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['confirm', 'cancel', 'update:show'])

function handleConfirm() {
  emit('confirm')
  emit('update:show', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:show', false)
}

const iconMap = {
  danger: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
  warning: 'M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z',
  info: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z',
}

const typeColors = {
  danger: {
    icon: 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400',
    button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white',
  },
  warning: {
    icon: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400',
    button: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500 text-white',
  },
  info: {
    icon: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400',
    button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white',
  },
}
</script>

<template>
  <Modal
    :show="show"
    :title="title"
    size="sm"
    @update:show="emit('update:show', $event)"
    @close="handleCancel"
  >
    <div class="flex items-start gap-4">
      <div
        v-if="icon || iconMap[type]"
        :class="['flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center', typeColors[type].icon]"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" :d="icon || iconMap[type]" />
        </svg>
      </div>
      <div class="flex-1">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {{ message }}
        </p>
      </div>
    </div>

    <template #footer>
      <button
        type="button"
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
        @click="handleCancel"
      >
        {{ cancelText }}
      </button>
      <button
        type="button"
        :class="[
          'px-4 py-2 text-sm font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors',
          typeColors[type].button,
        ]"
        @click="handleConfirm"
      >
        {{ confirmText }}
      </button>
    </template>
  </Modal>
</template>
