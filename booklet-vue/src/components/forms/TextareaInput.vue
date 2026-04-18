<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
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
  rows: {
    type: Number,
    default: 4,
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
  maxLength: {
    type: Number,
    default: 0,
  },
  autoResize: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const inputId = computed(() => props.name || props.label || 'textarea')
const charCount = computed(() => props.modelValue?.length || 0)

const textareaClasses = computed(() => {
  const base = 'block w-full px-3 py-2.5 text-sm rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 resize-y'

  if (props.error) {
    return `${base} border-red-500 dark:border-red-500 text-red-900 dark:text-red-300 placeholder-red-400 dark:placeholder-red-500 bg-red-50 dark:bg-red-900/20 focus:ring-red-500 focus:border-red-500`
  }

  if (props.disabled) {
    return `${base} border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed`
  }

  return `${base} border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500`
})

function onInput(event) {
  emit('update:modelValue', event.target.value)
  if (props.autoResize) {
    autoResize()
  }
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.max(el.scrollHeight, 0) + 'px'
}

watch(
  () => props.modelValue,
  () => {
    if (props.autoResize) {
      nextTick(autoResize)
    }
  }
)

onMounted(() => {
  if (props.autoResize) {
    nextTick(autoResize)
  }
})
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

    <!-- Textarea -->
    <textarea
      :id="inputId"
      ref="textareaRef"
      :name="name"
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :maxlength="maxLength || undefined"
      :class="textareaClasses"
      @input="onInput"
    />

    <!-- Bottom Row -->
    <div class="flex items-center justify-between mt-1.5">
      <div>
        <!-- Error Message -->
        <p v-if="error" class="text-sm text-red-600 dark:text-red-400">
          {{ error }}
        </p>
        <!-- Help Text -->
        <p v-else-if="helpText" class="text-sm text-gray-500 dark:text-gray-400">
          {{ helpText }}
        </p>
      </div>

      <!-- Character Count -->
      <p
        v-if="maxLength > 0"
        :class="[
          'text-xs',
          charCount > maxLength * 0.9 ? 'text-amber-500' : 'text-gray-400 dark:text-gray-500',
        ]"
      >
        {{ charCount }} / {{ maxLength }}
      </p>
    </div>
  </div>
</template>
