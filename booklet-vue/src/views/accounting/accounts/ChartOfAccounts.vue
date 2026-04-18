<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Modal from '@/components/common/Modal.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { listAccounts, createAccount } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const accounts = ref([])
const loading = ref(true)
const submitting = ref(false)

// Expanded groups
const expandedGroups = ref({
  asset: true,
  liability: false,
  equity: false,
  revenue: false,
  expense: false,
})

// Create account modal
const showCreateModal = ref(false)
const createErrors = ref({})
const createForm = ref({
  code: '',
  name: '',
  type: '',
  parent_id: '',
  description: '',
})

const accountTypeOptions = [
  { value: 'asset', label: 'Asset' },
  { value: 'liability', label: 'Liability' },
  { value: 'equity', label: 'Equity' },
  { value: 'revenue', label: 'Revenue' },
  { value: 'expense', label: 'Expense' },
]

const groupLabels = {
  asset: 'Assets',
  liability: 'Liabilities',
  equity: 'Equity',
  revenue: 'Revenue',
  expense: 'Expenses',
}

const groupColors = {
  // asset: {
  //   header: 'bg-green-50 dark:bg-green-100/20 border-green-200 dark:border-green-800',
  //   icon: 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/40',
  //   text: 'text-green-700 dark:text-green-400',
  // },
  // liability: {
  //   header: 'bg-red-50 dark:bg-red-100/20 border-red-200 dark:border-red-800',
  //   icon: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/40',
  //   text: 'text-red-700 dark:text-red-400',
  // },
  // equity: {
  //   header: 'bg-purple-50 dark:bg-purple-100/20 border-purple-200 dark:border-purple-800',
  //   icon: 'text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/40',
  //   text: 'text-purple-700 dark:text-purple-400',
  // },
  asset: {
    header: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
    icon: 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/40',
    text: 'text-emerald-700 dark:text-emerald-400',
  },
  liability: {
    header: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
    icon: 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/40',
    text: 'text-amber-700 dark:text-amber-400',
  },
  equity: {
    header: 'bg-slate-50 dark:bg-slate-900/20 border-slate-200 dark:border-slate-800',
    icon: 'text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-900/40',
    text: 'text-slate-700 dark:text-slate-400',
  },

  revenue: {
    header: 'bg-cyan-50 dark:bg-cyan-900/20 border-cyan-200 dark:border-cyan-800',
    icon: 'text-cyan-600 dark:text-cyan-400 bg-cyan-100 dark:bg-cyan-900/40',
    text: 'text-cyan-700 dark:text-cyan-400',
  },
  expense: {
    header: 'bg-rose-50 dark:bg-rose-900/20 border-rose-200 dark:border-rose-800',
    icon: 'text-rose-600 dark:text-rose-400 bg-rose-100 dark:bg-rose-900/40',
    text: 'text-rose-700 dark:text-rose-400',
  },

}

const groupedAccounts = computed(() => {
  const groups = { asset: [], liability: [], equity: [], revenue: [], expense: [] }
  for (const account of accounts.value) {
    const type = (account.type || '').toLowerCase()
    if (groups[type]) {
      groups[type].push(account)
    }
  }
  // Sort each group by code
  for (const key of Object.keys(groups)) {
    groups[key].sort((a, b) => (a.code || '').localeCompare(b.code || ''))
  }
  return groups
})

const parentAccountOptions = computed(() => {
  return accounts.value
    .filter((a) => String(a.id) !== String(createForm.value.parent_id))
    .map((a) => ({
      value: String(a.id),
      label: `${a.code || ''} — ${a.name || ''}`,
    }))
})

function toggleGroup(group) {
  expandedGroups.value[group] = !expandedGroups.value[group]
}

function viewAccount(account) {
  router.push({ name: 'AccountDetail', params: { id: account.id } })
}

function openCreateModal() {
  createForm.value = { code: '', name: '', type: '', parent_id: '', description: '' }
  createErrors.value = {}
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
  createForm.value = { code: '', name: '', type: '', parent_id: '', description: '' }
  createErrors.value = {}
}

function validateCreate() {
  const newErrors = {}
  if (!createForm.value.code?.trim()) {
    newErrors.code = 'Account code is required'
  }
  if (!createForm.value.name?.trim()) {
    newErrors.name = 'Account name is required'
  }
  if (!createForm.value.type) {
    newErrors.type = 'Account type is required'
  }
  createErrors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleCreate() {
  if (!validateCreate()) return

  submitting.value = true
  try {
    const payload = {
      code: createForm.value.code,
      name: createForm.value.name,
      type: createForm.value.type,
      description: createForm.value.description,
    }
    if (createForm.value.parent_id) {
      payload.parent_id = createForm.value.parent_id
    }
    await createAccount(payload)
    toast.show('Account created successfully', 'success')
    closeCreateModal()
    await fetchAccounts()
  } catch (error) {
    console.error('Failed to create account:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create account'
    toast.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

async function fetchAccounts() {
  loading.value = true
  try {
    const { data } = await listAccounts()
    accounts.value = Array.isArray(data) ? data : data.items || data.accounts || []
  } catch (error) {
    console.error('Failed to fetch accounts:', error)
    accounts.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAccounts()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Chart of Accounts"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Chart of Accounts' }
      ]"
    >
      <template #actions>
        <button
          v-if="auth.hasPermission('accounts:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          @click="openCreateModal"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Account
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading chart of accounts..." />

    <EmptyState
      v-else-if="accounts.length === 0"
      title="No accounts yet"
      message="Get started by creating your first account in the chart of accounts."
      :action-text="auth.hasPermission('accounts:create') ? 'New Account' : ''"
      :action-route="auth.hasPermission('accounts:create') ? undefined : undefined"
      @action="openCreateModal"
    />

    <template v-else>
      <!-- Grouped Account Sections -->
      <div v-for="(group, type) in groupedAccounts" :key="type" class="mb-4">
        <div
          :class="[
            'rounded-lg border overflow-hidden',
            groupColors[type]?.header || 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
          ]"
        >
          <!-- Group Header -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-6 py-4 transition-colors"
            @click="toggleGroup(type)"
          >
            <div class="flex items-center gap-3">
              <svg
                :class="[
                  'w-5 h-5 transition-transform duration-200',
                  expandedGroups[type] ? 'rotate-90' : '',
                  groupColors[type]?.text || 'text-gray-500 dark:text-gray-400'
                ]"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
              <h3
                :class="[
                  'text-base font-semibold',
                  groupColors[type]?.text || 'text-gray-900 dark:text-white'
                ]"
              >
                {{ groupLabels[type] || type }}
              </h3>
              <span class="text-xs px-2 py-0.5 rounded-full bg-white/60 dark:bg-gray-700 font-medium" :class="groupColors[type]?.text || 'text-gray-500 dark:text-gray-400'">
                {{ group.length }}
              </span>
            </div>
          </button>

          <!-- Collapsible Account List -->
          <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="max-h-0 opacity-0"
            enter-to-class="max-h-[2000px] opacity-100"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="max-h-[2000px] opacity-100"
            leave-to-class="max-h-0 opacity-0"
          >
            <div v-show="expandedGroups[type]" class="overflow-hidden">
              <div class="border-t" :class="groupColors[type]?.header ? 'border-white/20 dark:border-gray-700/50' : 'border-gray-200 dark:border-gray-700'">
                <!-- Table Header -->
                <div class="grid grid-cols-12 gap-4 px-6 py-2.5 bg-gray-50 dark:bg-gray-800 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  <div class="col-span-2">Code</div>
                  <div class="col-span-4">Name</div>
                  <div class="col-span-2">Type</div>
                  <div class="col-span-2 text-right">Balance</div>
                  <div class="col-span-2 text-right">Actions</div>
                </div>

                <!-- Account Rows -->
                <div
                  v-for="account in group"
                  :key="account.id"
                  class="grid grid-cols-12 gap-4 px-6 py-3 hover:bg-gray-0 dark:hover:bg-gray-800 transition-colors cursor-pointer border-b border-gray-100 dark:border-gray-700/50 last:border-b-0"
                  @click="viewAccount(account)"
                >
                  <div class="col-span-2">
                    <span class="text-sm font-mono text-gray-700 dark:text-gray-300">{{ account.code || '—' }}</span>
                  </div>
                  <div class="col-span-4">
                    <span class="text-sm font-medium text-gray-900 dark:text-white">{{ account.name || '—' }}</span>
                    <p v-if="account.description" class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ account.description }}</p>
                  </div>
                  <div class="col-span-2">
                    <span class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 capitalize">
                      {{ account.type || '—' }}
                    </span>
                  </div>
                  <div class="col-span-2 text-right">
                    <span
                      class="text-sm font-semibold"
                      :class="(account.balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
                    >
                      {{ formatCurrency(account.balance || 0, auth.branchCurrency) }}
                    </span>
                  </div>
                  <div class="col-span-2 text-right">
                    <button
                      type="button"
                      class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                      title="View Details"
                      @click.stop="viewAccount(account)"
                    >
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Empty Group -->
                <div
                  v-if="group.length === 0"
                  class="px-6 py-6 text-center text-sm text-gray-400 dark:text-gray-500"
                >
                  No accounts in this category
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </template>

    <!-- Create Account Modal -->
    <Modal
      v-model:show="showCreateModal"
      title="Create Account"
      size="md"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput
            v-model="createForm.code"
            label="Account Code"
            name="code"
            placeholder="e.g., 1001"
            :required="true"
            :error="createErrors.code"
          />

          <SelectInput
            v-model="createForm.type"
            label="Account Type"
            name="type"
            :options="accountTypeOptions"
            placeholder="Select type"
            :required="true"
            :error="createErrors.type"
          />
        </div>

        <TextInput
          v-model="createForm.name"
          label="Account Name"
          name="name"
          placeholder="e.g., Cash in Bank"
          :required="true"
          :error="createErrors.name"
        />

        <SelectInput
          v-model="createForm.parent_id"
          label="Parent Account"
          name="parent_id"
          :options="parentAccountOptions"
          placeholder="None (Top-level account)"
          help-text="Leave blank for a top-level account"
        />

        <TextareaInput
          v-model="createForm.description"
          label="Description"
          name="description"
          placeholder="Optional description of this account"
          :rows="2"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closeCreateModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="submitting"
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleCreate"
        >
          {{ submitting ? 'Creating...' : 'Create Account' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
