<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'email', 'password', 'number', 'tel', 'url'].includes(v),
  },
  placeholder: {
    type: String,
    default: '',
  },
  required: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  helpText: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const inputId = computed(() => props.name || props.label || 'input')

const inputClasses = computed(() => {
  const base = 'block w-full text-sm rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0'

  const hasIcon = !!props.icon
  const paddingLeft = hasIcon ? 'pl-10' : 'pl-3'

  const paddingRight = 'pr-3'
  const paddingY = 'py-2.5'

  if (props.error) {
    return `${base} ${paddingLeft} ${paddingRight} ${paddingY} border-red-500 dark:border-red-500 text-red-900 dark:text-red-300 placeholder-red-400 dark:placeholder-red-500 bg-red-50 dark:bg-red-900/20 focus:ring-red-500 focus:border-red-500`
  }

  if (props.disabled) {
    return `${base} ${paddingLeft} ${paddingRight} ${paddingY} border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed`
  }

  return `${base} ${paddingLeft} ${paddingRight} ${paddingY} border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500`
})

function onInput(event) {
  const value = props.type === 'number' ? (event.target.value === '' ? '' : Number(event.target.value)) : event.target.value
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="w-full">
    <!-- Label -->
    <label
      v-if="label"
      :for="inputId"
      class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
    >
      {{ label }}
      <span v-if="required" class="text-red-500 ml-0.5">*</span>
    </label>

    <!-- Input Wrapper -->
    <div class="relative">
      <!-- Left Icon -->
      <div
        v-if="icon"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none"
      >
        <svg
          class="w-5 h-5 text-gray-400 dark:text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
        </svg>
      </div>

      <input
        :id="inputId"
        :type="type"
        :name="name"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :class="inputClasses"
        @input="onInput"
      />
    </div>

    <!-- Error Message -->
    <p v-if="error" class="mt-1.5 text-sm text-red-600 dark:text-red-400">
      {{ error }}
    </p>

    <!-- Help Text -->
    <p v-else-if="helpText" class="mt-1.5 text-sm text-gray-500 dark:text-gray-400">
      {{ helpText }}
    </p>
  </div>
</template>
