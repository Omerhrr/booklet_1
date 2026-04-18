<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Array],
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
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Select an option...',
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
  multiple: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectRef = ref(null)

const selectId = computed(() => props.name || props.label || 'select')

const displayValue = computed(() => {
  if (props.multiple && Array.isArray(props.modelValue)) {
    return props.modelValue
      .map(val => props.options.find(o => o.value === val)?.label || val)
      .join(', ')
  }
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : ''
})

const selectedOptions = computed(() => {
  if (props.multiple && Array.isArray(props.modelValue)) {
    return props.options.filter(o => props.modelValue.includes(o.value))
  }
  return []
})

function selectOption(option) {
  if (props.multiple) {
    const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    const index = current.indexOf(option.value)
    if (index > -1) {
      current.splice(index, 1)
    } else {
      current.push(option.value)
    }
    emit('update:modelValue', current)
  } else {
    emit('update:modelValue', option.value)
    isOpen.value = false
  }
}

function toggleDropdown() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function onClickOutside(event) {
  if (selectRef.value && !selectRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

function removeMultiple(value) {
  if (Array.isArray(props.modelValue)) {
    emit('update:modelValue', props.modelValue.filter(v => v !== value))
  }
}
</script>

<template>
  <div class="w-full" @click.outside="onClickOutside">
    <!-- Label -->
    <label
      v-if="label"
      :for="selectId"
      class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
    >
      {{ label }}
      <span v-if="required" class="text-red-500 ml-0.5">*</span>
    </label>

    <!-- Select Wrapper -->
    <div ref="selectRef" class="relative">
      <!-- Multi-value Tags -->
      <div
        v-if="multiple && selectedOptions.length > 0"
        class="flex flex-wrap gap-1 mb-1"
      >
        <span
          v-for="opt in selectedOptions"
          :key="opt.value"
          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400 rounded-md"
        >
          {{ opt.label }}
          <button
            type="button"
            class="hover:text-blue-600 dark:hover:text-blue-300 transition-colors"
            @click.stop="removeMultiple(opt.value)"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </span>
      </div>

      <!-- Trigger -->
      <button
        type="button"
        :disabled="disabled"
        :class="[
          'relative w-full flex items-center justify-between text-left rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-red-500 dark:border-red-500 bg-red-50 dark:bg-red-900/20 focus:ring-red-500 focus:border-red-500'
            : disabled
              ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:ring-blue-500 focus:border-blue-500',
          multiple ? 'py-1.5 pl-3 pr-10' : 'py-2.5 pl-3 pr-10',
        ]"
        @click="toggleDropdown"
      >
        <span
          :class="[
            'block truncate text-sm',
            (modelValue === '' || modelValue === undefined || modelValue === null || (Array.isArray(modelValue) && modelValue.length === 0))
              ? 'text-gray-400 dark:text-gray-500'
              : 'text-gray-900 dark:text-white',
          ]"
        >
          {{ displayValue || placeholder }}
        </span>

        <!-- Chevron -->
        <svg
          :class="[
            'absolute right-3 w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform',
            isOpen ? 'rotate-180' : '',
          ]"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      <!-- Dropdown -->
      <Transition
        enter-active-class="transition ease-out duration-100"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition ease-in duration-75"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="isOpen"
          class="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto"
        >
          <!-- No Options -->
          <div
            v-if="options.length === 0"
            class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400"
          >
            No options available
          </div>

          <template v-else>
            <button
              v-for="option in options"
              :key="option.value"
              type="button"
              :class="[
                'w-full flex items-center gap-2 px-3 py-2 text-left text-sm transition-colors',
                (multiple && Array.isArray(modelValue) && modelValue.includes(option.value)) || (!multiple && modelValue === option.value)
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
              ]"
              @click.stop="selectOption(option)"
            >
              <!-- Checkbox for multiple -->
              <svg
                v-if="multiple"
                :class="[
                  'w-4 h-4 rounded border transition-colors',
                  Array.isArray(modelValue) && modelValue.includes(option.value)
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'border-gray-300 dark:border-gray-600',
                ]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  v-if="Array.isArray(modelValue) && modelValue.includes(option.value)"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M4.5 12.75l6 6 9-13.5"
                />
                <rect v-else x="3" y="3" width="18" height="18" rx="2" ry="2" />
              </svg>
              {{ option.label }}
            </button>
          </template>
        </div>
      </Transition>
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
