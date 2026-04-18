<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getAgentSettings, updateAgentSettings } from '@/api/agents'

const loading = ref(true)
const saving = ref(false)

const settings = ref({
  automation: { enabled: true, schedule: 'manual', config: {} },
  audit: { enabled: true, schedule: 'weekly', config: {} },
  wizard: { enabled: true, config: {} },
})

async function fetchSettings() {
  loading.value = true
  try {
    const { data } = await getAgentSettings()
    if (data) {
      if (data.automation) settings.value.automation = { ...settings.value.automation, ...data.automation }
      if (data.audit) settings.value.audit = { ...settings.value.audit, ...data.audit }
      if (data.wizard) settings.value.wizard = { ...settings.value.wizard, ...data.wizard }
    }
  } catch (error) {
    console.error('Failed to fetch agent settings:', error)
  } finally {
    loading.value = false
  }
}

async function saveAllSettings() {
  saving.value = true
  try {
    await updateAgentSettings(settings.value)
  } catch (error) {
    console.error('Failed to save agent settings:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => { fetchSettings() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Agent Settings"
      subtitle="Configure AI agent behavior and scheduling"
      :breadcrumbs="[
        { text: 'Agents', to: { name: 'AgentDashboard' } },
        { text: 'Settings' },
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          :disabled="saving"
          @click="saveAllSettings"
        >
          {{ saving ? 'Saving...' : 'Save All' }}
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" size="lg" text="Loading settings..." />

    <template v-else>
      <div class="space-y-6 max-w-3xl">
        <!-- Automation Agent -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-semibold text-gray-900 dark:text-white">Automation Agent</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">Automate repetitive tasks</p>
              </div>
            </div>
            <button
              type="button"
              :class="['relative w-11 h-6 rounded-full transition-colors', settings.automation.enabled ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-gray-600']"
              @click="settings.automation.enabled = !settings.automation.enabled"
            >
              <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', settings.automation.enabled ? 'translate-x-5.5' : 'translate-x-0.5']" />
            </button>
          </div>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Schedule</label>
              <select v-model="settings.automation.schedule" class="block w-full max-w-xs px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors">
                <option value="manual">Manual Only</option>
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Audit Agent -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400 flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-semibold text-gray-900 dark:text-white">Audit Agent</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">Review financial records</p>
              </div>
            </div>
            <button
              type="button"
              :class="['relative w-11 h-6 rounded-full transition-colors', settings.audit.enabled ? 'bg-amber-500' : 'bg-gray-300 dark:bg-gray-600']"
              @click="settings.audit.enabled = !settings.audit.enabled"
            >
              <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', settings.audit.enabled ? 'translate-x-5.5' : 'translate-x-0.5']" />
            </button>
          </div>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Schedule</label>
              <select v-model="settings.audit.schedule" class="block w-full max-w-xs px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors">
                <option value="manual">Manual Only</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Document Wizard -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400 flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-semibold text-gray-900 dark:text-white">Document Wizard</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">AI-powered document generation</p>
              </div>
            </div>
            <button
              type="button"
              :class="['relative w-11 h-6 rounded-full transition-colors', settings.wizard.enabled ? 'bg-violet-500' : 'bg-gray-300 dark:bg-gray-600']"
              @click="settings.wizard.enabled = !settings.wizard.enabled"
            >
              <span :class="['absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', settings.wizard.enabled ? 'translate-x-5.5' : 'translate-x-0.5']" />
            </button>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            The Document Wizard uses AI to generate business documents. When enabled, users can start sessions to create invoices, contracts, reports, and other documents.
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
