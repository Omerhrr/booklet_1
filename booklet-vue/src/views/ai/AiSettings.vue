<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getAiSettings, updateAiSettings, getAiProviders } from '@/api/ai'

const loading = ref(true)
const saving = ref(false)
const providers = ref([])
const form = ref({
  api_key: '',
  model: '',
  temperature: 0.7,
  provider: '',
})

const providerOptions = ref([])
const modelOptions = ref([])

async function fetchSettings() {
  loading.value = true
  try {
    const [settingsRes, providersRes] = await Promise.all([
      getAiSettings(),
      getAiProviders(),
    ])
    const settings = settingsRes.data
    form.value = {
      api_key: settings.api_key || '',
      model: settings.model || '',
      temperature: settings.temperature ?? 0.7,
      provider: settings.provider || '',
    }
    providers.value = Array.isArray(providersRes.data) ? providersRes.data : providersRes.data.providers || providersRes.data.items || []
    providerOptions.value = providers.value.map(p => ({ value: p.id || p.name, label: p.name || p.label }))
    updateModelOptions()
  } catch (error) {
    console.error('Failed to fetch AI settings:', error)
  } finally {
    loading.value = false
  }
}

function updateModelOptions() {
  const provider = providers.value.find(p => (p.id || p.name) === form.value.provider)
  if (provider && provider.models) {
    modelOptions.value = provider.models.map(m => ({ value: m.id || m, label: m.name || m }))
  } else {
    modelOptions.value = [
      { value: 'gpt-4', label: 'GPT-4' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
      { value: 'claude-3-opus', label: 'Claude 3 Opus' },
      { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
    ]
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await updateAiSettings({
      api_key: form.value.api_key,
      model: form.value.model,
      temperature: form.value.temperature,
      provider: form.value.provider,
    })
  } catch (error) {
    console.error('Failed to save AI settings:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="AI Settings"
      subtitle="Configure AI provider and model settings"
      :breadcrumbs="[
        { text: 'AI', to: { name: 'AiChat' } },
        { text: 'Settings' },
      ]"
    />

    <LoadingSpinner v-if="loading" size="lg" text="Loading settings..." />

    <template v-else>
      <div class="max-w-2xl mx-auto space-y-6">
        <!-- Provider Settings -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-5">
          <div>
            <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1">Provider Configuration</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Configure the AI provider and API settings for your organization.</p>
          </div>

          <SelectInput
            v-model="form.provider"
            label="AI Provider"
            name="provider"
            :options="providerOptions"
            placeholder="Select a provider..."
            @update:model-value="updateModelOptions"
          />

          <TextInput
            v-model="form.api_key"
            label="API Key"
            name="api_key"
            type="password"
            placeholder="Enter your API key"
            help-text="Your API key is encrypted and stored securely."
          />

          <SelectInput
            v-model="form.model"
            label="Model"
            name="model"
            :options="modelOptions"
            placeholder="Select a model..."
          />

          <!-- Temperature Slider -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Temperature
              <span class="ml-2 text-xs text-gray-400">{{ form.temperature }}</span>
            </label>
            <input
              v-model.number="form.temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
            <div class="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1">
              <span>Precise (0)</span>
              <span>Balanced (1)</span>
              <span>Creative (2)</span>
            </div>
          </div>
        </div>

        <!-- Save/Cancel -->
        <div class="flex items-center justify-end gap-3">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="fetchSettings"
          >
            Cancel
          </button>
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            :disabled="saving"
            @click="saveSettings"
          >
            {{ saving ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
