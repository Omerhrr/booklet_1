<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getConfigurations, listFindings, getExecutions } from '@/api/agents'
import { formatRelative } from '@/utils/dates'

const router = useRouter()
const loading = ref(true)
const findingsCount = ref(0)
const automationLastRun = ref(null)
const auditLastRun = ref(null)

const agentCards = ref([
  {
    id: 'automation',
    title: 'Automation Agent',
    description: 'Automate repetitive tasks like invoice processing, data reconciliation, and workflow triggers.',
    icon: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z',
    route: { name: 'AutomationAgent' },
    color: 'emerald',
    lastRun: null,
  },
  {
    id: 'audit',
    title: 'Audit Agent',
    description: 'Review your financial records for anomalies, compliance issues, and potential fraud indicators.',
    icon: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
    route: { name: 'AuditAgent' },
    color: 'amber',
    lastRun: null,
  },
  {
    id: 'wizard',
    title: 'Document Wizard',
    description: 'Generate business documents like invoices, contracts, and reports using AI-powered templates.',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    route: { name: 'DocWizard' },
    color: 'violet',
    lastRun: null,
  },
  {
    id: 'findings',
    title: 'Findings',
    description: 'Review all agent-generated findings, resolve issues, and track resolution status.',
    icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
    route: { name: 'FindingsList' },
    color: 'rose',
    badge: 0,
  },
  {
    id: 'settings',
    title: 'Settings',
    description: 'Configure agent behavior, scheduling, thresholds, and enable/disable specific agents.',
    icon: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z',
    route: { name: 'AgentSettings' },
    color: 'gray',
    lastRun: null,
  },
])

const colorMap = {
  emerald: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400',
  amber: 'bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400',
  violet: 'bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400',
  rose: 'bg-rose-100 text-rose-600 dark:bg-rose-900/40 dark:text-rose-400',
  gray: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
}

const borderMap = {
  emerald: 'border-emerald-200 dark:border-emerald-800',
  amber: 'border-amber-200 dark:border-amber-800',
  violet: 'border-violet-200 dark:border-violet-800',
  rose: 'border-rose-200 dark:border-rose-800',
  gray: 'border-gray-200 dark:border-gray-700',
}

const btnColorMap = {
  emerald: 'bg-emerald-600 hover:bg-emerald-700',
  amber: 'bg-amber-600 hover:bg-amber-700',
  violet: 'bg-violet-600 hover:bg-violet-700',
  rose: 'bg-rose-600 hover:bg-rose-700',
  gray: 'bg-gray-600 hover:bg-gray-700',
}

async function fetchData() {
  loading.value = true
  try {
    const [findingsRes, execsRes] = await Promise.allSettled([
      listFindings({ status: 'open' }),
      getExecutions({ page_size: 10 }),
    ])
    if (findingsRes.status === 'fulfilled') {
      const data = findingsRes.value.data
      const items = Array.isArray(data) ? data : data.items || []
      findingsCount.value = data.total || items.length
      const findingsCard = agentCards.value.find(c => c.id === 'findings')
      if (findingsCard) findingsCard.badge = findingsCount.value
    }
    if (execsRes.status === 'fulfilled') {
      const data = execsRes.value.data
      const items = Array.isArray(data) ? data : data.items || []
      const autoExec = items.find(e => e.agent_type === 'automation')
      const auditExec = items.find(e => e.agent_type === 'audit')
      if (autoExec) agentCards.value.find(c => c.id === 'automation').lastRun = autoExec.created_at || autoExec.started_at
      if (auditExec) agentCards.value.find(c => c.id === 'audit').lastRun = auditExec.created_at || auditExec.started_at
    }
  } catch (error) {
    console.error('Failed to fetch agent data:', error)
  } finally {
    loading.value = false
  }
}

function getActionText(card) {
  if (card.id === 'wizard') return 'Start'
  if (card.id === 'findings') return 'View'
  if (card.id === 'settings') return 'Configure'
  return 'Run'
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="AI Agents" subtitle="Automate tasks, audit records, and generate documents" />

    <LoadingSpinner v-if="loading" size="lg" text="Loading agents..." />

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="card in agentCards"
        :key="card.id"
        :class="[
          'relative flex flex-col p-6 rounded-xl border bg-white dark:bg-gray-800 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg',
          borderMap[card.color],
        ]"
      >
        <!-- Badge -->
        <div v-if="card.badge > 0" class="absolute -top-2 -right-2">
          <span class="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-white bg-rose-500 rounded-full">
            {{ card.badge }}
          </span>
        </div>

        <!-- Icon -->
        <div :class="['w-12 h-12 rounded-lg flex items-center justify-center mb-4', colorMap[card.color]]">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" :d="card.icon" />
          </svg>
        </div>

        <!-- Content -->
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1">{{ card.title }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-3">{{ card.description }}</p>

        <!-- Last Run -->
        <p v-if="card.lastRun" class="text-xs text-gray-400 dark:text-gray-500 mb-4">
          Last run: {{ formatRelative(card.lastRun) }}
        </p>
        <div v-else class="mb-4" />

        <!-- Action -->
        <router-link
          :to="card.route"
          :class="[
            'mt-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white rounded-lg transition-colors',
            btnColorMap[card.color],
          ]"
        >
          {{ getActionText(card) }}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </router-link>
      </div>
    </div>
  </div>
</template>
