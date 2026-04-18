<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  accept: {
    type: String,
    default: '*',
  },
  maxSize: {
    type: Number,
    default: 10,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: 'Upload files',
  },
  helpText: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['fileSelected', 'error'])

const isDragging = ref(false)
const files = ref([])
const previewUrls = ref({})
const inputRef = ref(null)

const maxSizeBytes = computed(() => props.maxSize * 1024 * 1024)

const acceptedTypes = computed(() => {
  return props.accept !== '*' ? props.accept.split(',').map(t => t.trim()) : null
})

function isAcceptedType(file) {
  if (!acceptedTypes.value) return true

  return acceptedTypes.value.some(type => {
    if (type.startsWith('.')) {
      return file.name.toLowerCase().endsWith(type.toLowerCase())
    }
    if (type.endsWith('/*')) {
      const category = type.replace('/*', '')
      return file.type.startsWith(category + '/')
    }
    return file.type === type
  })
}

function validateFile(file) {
  if (!isAcceptedType(file)) {
    emit('error', `File type "${file.type || file.name.split('.').pop()}" is not supported.`)
    return false
  }
  if (file.size > maxSizeBytes.value) {
    emit('error', `File "${file.name}" exceeds the maximum size of ${props.maxSize}MB.`)
    return false
  }
  return true
}

function handleFiles(fileList) {
  const newFiles = []
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i]
    if (validateFile(file)) {
      newFiles.push(file)
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          previewUrls.value[file.name] = e.target.result
        }
        reader.readAsDataURL(file)
      }
    }
  }

  if (props.multiple) {
    files.value = [...files.value, ...newFiles]
  } else {
    files.value = newFiles.slice(0, 1)
  }

  if (newFiles.length > 0) {
    emit('fileSelected', props.multiple ? files.value : files.value[0])
  }
}

function onDrop(event) {
  isDragging.value = false
  const dt = event.dataTransfer
  if (dt.files && dt.files.length > 0) {
    handleFiles(dt.files)
  }
}

function onDragOver(event) {
  event.preventDefault()
  isDragging.value = true
}

function onDragLeave(event) {
  event.preventDefault()
  isDragging.value = false
}

function onFileChange(event) {
  if (event.target.files && event.target.files.length > 0) {
    handleFiles(event.target.files)
  }
}

function triggerBrowse() {
  inputRef.value?.click()
}

function removeFile(index) {
  const fileName = files.value[index].name
  files.value.splice(index, 1)
  delete previewUrls.value[fileName]
  emit('fileSelected', props.multiple ? files.value : (files.value[0] || null))
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<template>
  <div class="w-full">
    <!-- Drop Zone -->
    <div
      :class="[
        'relative flex flex-col items-center justify-center w-full min-h-[120px] border-2 border-dashed rounded-lg cursor-pointer transition-colors',
        isDragging
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
          : 'border-gray-300 bg-gray-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700',
      ]"
      @click="triggerBrowse"
      @drop="onDrop"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
    >
      <input
        ref="inputRef"
        type="file"
        :accept="accept"
        :multiple="multiple"
        class="hidden"
        @change="onFileChange"
      />

      <div class="flex flex-col items-center gap-2 py-4">
        <svg
          class="w-8 h-8 text-gray-400 dark:text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        <div class="text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            <span class="font-semibold text-blue-600 dark:text-blue-400">{{ label }}</span>
            or drag and drop
          </p>
          <p v-if="helpText" class="mt-1 text-xs text-gray-500 dark:text-gray-500">
            {{ helpText }}
          </p>
        </div>
      </div>
    </div>

    <!-- File List -->
    <ul v-if="files.length > 0" class="mt-3 space-y-2">
      <li
        v-for="(file, index) in files"
        :key="index"
        class="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
      >
        <!-- Image Preview -->
        <div
          v-if="previewUrls[file.name]"
          class="flex-shrink-0 w-10 h-10 rounded-md overflow-hidden bg-gray-100 dark:bg-gray-700"
        >
          <img :src="previewUrls[file.name]" :alt="file.name" class="w-full h-full object-cover" />
        </div>
        <!-- File Icon -->
        <div
          v-else
          class="flex-shrink-0 w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-700 flex items-center justify-center"
        >
          <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>

        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ file.name }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ formatFileSize(file.size) }}</p>
        </div>

        <button
          type="button"
          class="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          @click="removeFile(index)"
          aria-label="Remove file"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </li>
    </ul>
  </div>
</template>
