<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getAnalyses, createDashboard } from '@/api/analytics'

const router = useRouter()
const saving = ref(false)
const analysesOptions = ref([])

const form = ref({
  name: '',
  description: '',
  analysisIds: [],
})

async function loadAnalyses() {
  try {
    const { data } = await getAnalyses()
    const items = Array.isArray(data) ? data : data.items || []
    analysesOptions.value = items.map(a => ({ value: a.id, label: a.name }))
  } catch (error) {
    console.error('Failed to load analyses:', error)
  }
}

async function handleSubmit() {
  if (!form.value.name) return
  saving.value = true
  try {
    await createDashboard({
      name: form.value.name,
      description: form.value.description,
      analysis_ids: form.value.analysisIds,
    })
    router.push({ name: 'DashboardList' })
  } catch (error) {
    console.error('Failed to create dashboard:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => { loadAnalyses() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="New Dashboard"
      subtitle="Create a new analytics dashboard"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Dashboards', to: { name: 'DashboardList' } },
        { text: 'New' },
      ]"
    />

    <div class="max-w-2xl mx-auto">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-5">
        <TextInput
          v-model="form.name"
          label="Dashboard Name"
          name="name"
          placeholder="e.g., Sales Overview"
          required
        />

        <TextareaInput
          v-model="form.description"
          label="Description"
          name="description"
          placeholder="What does this dashboard show?"
        />

        <SelectInput
          v-model="form.analysisIds"
          label="Add Analyses"
          name="analyses"
          :options="analysesOptions"
          placeholder="Select analyses to include..."
          multiple
        />

        <!-- Layout Preview -->
        <div v-if="form.analysisIds.length > 0" class="border-t border-gray-200 dark:border-gray-700 pt-4">
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Layout Preview</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              v-for="id in form.analysisIds"
              :key="id"
              class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
            >
              <div class="flex items-center gap-2 mb-2">
                <div class="w-3 h-3 rounded-full bg-violet-400" />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {{ analysesOptions.find(a => a.value === id)?.label || 'Analysis' }}
                </span>
              </div>
              <div class="h-24 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                <svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="router.back()"
          >
            Cancel
          </button>
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 transition-colors"
            :disabled="!form.name || saving"
            @click="handleSubmit"
          >
            {{ saving ? 'Creating...' : 'Create Dashboard' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
