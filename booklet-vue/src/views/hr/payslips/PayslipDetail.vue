<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'
import * as hrApi from '@/api/hr'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const payslip = ref(null)
const loading = ref(true)
const markingPaid = ref(false)
const exportingPdf = ref(false)

const breadcrumbs = computed(() => [
  { text: 'HR', to: '/hr' },
  { text: 'Payslips', to: '/hr/payslips' },
  { text: payslip.value ? `${payslip.value.employee_name} - ${payslip.value.month_name} ${payslip.value.year}` : 'Payslip Details' },
])

const statusVariantMap = {
  pending: 'warning',
  paid: 'success',
}

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

async function fetchPayslip() {
  loading.value = true
  try {
    const { data } = await hrApi.getPayslip(route.params.id)
    payslip.value = data
  } catch (error) {
    console.error('Failed to fetch payslip:', error)
    toastStore.show('Failed to load payslip', 'error')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'PayslipList' })
}

async function markAsPaid() {
  markingPaid.value = true
  try {
    await hrApi.markPayslipPaid(route.params.id)
    payslip.value.status = 'paid'
    toastStore.show('Payslip marked as paid')
  } catch (error) {
    console.error('Failed to mark payslip as paid:', error)
    toastStore.show('Failed to update payslip status', 'error')
  } finally {
    markingPaid.value = false
  }
}

async function exportPdf() {
  exportingPdf.value = true
  try {
    // Generate a simple PDF-like download using the data
    const ps = payslip.value
    const content = [
      `PAYSLIP`,
      `${'='.repeat(60)}`,
      `Employee: ${ps.employee_name}`,
      `Period: ${ps.month_name} ${ps.year}`,
      `Status: ${ps.status.toUpperCase()}`,
      '',
      `EARNINGS`,
      `${'-'.repeat(40)}`,
      `Basic Salary:        ${formatAmount(ps.basic_salary)}`,
      `Housing Allowance:   ${formatAmount(ps.housing_allowance || 0)}`,
      `Transport Allowance: ${formatAmount(ps.transport_allowance || 0)}`,
      `Medical Allowance:   ${formatAmount(ps.medical_allowance || 0)}`,
      `Other Allowances:    ${formatAmount(ps.other_allowances || 0)}`,
      `${'-'.repeat(40)}`,
      `Total Earnings:      ${formatAmount(ps.gross_pay)}`,
      '',
      `DEDUCTIONS`,
      `${'-'.repeat(40)}`,
      `Tax:                 ${formatAmount(ps.tax)}`,
      `Pension:             ${formatAmount(ps.pension)}`,
      `Other Deductions:    ${formatAmount(ps.other_deductions || 0)}`,
      `${'-'.repeat(40)}`,
      `Total Deductions:    ${formatAmount(ps.total_deductions)}`,
      '',
      `NET PAY:             ${formatAmount(ps.net_pay)}`,
      `${'='.repeat(60)}`,
    ].join('\n')

    const blob = new Blob([content], { type: 'text/plain' })
    downloadBlob(blob, `Payslip_${ps.employee_name}_${ps.month_name}_${ps.year}.txt`)
    toastStore.show('Payslip exported')
  } catch (error) {
    console.error('Failed to export payslip:', error)
    toastStore.show('Failed to export payslip', 'error')
  } finally {
    exportingPdf.value = false
  }
}

onMounted(fetchPayslip)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading payslip..." />
    </div>

    <template v-else-if="payslip">
      <PageHeader title="Payslip Details" :breadcrumbs="breadcrumbs">
        <template #actions>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="goBack"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back
            </button>

            <button
              v-if="payslip.status === 'pending'"
              type="button"
              :disabled="markingPaid"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-green-700 bg-green-50 border border-green-300 rounded-lg hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700 dark:hover:bg-green-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="markAsPaid"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ markingPaid ? 'Updating...' : 'Mark as Paid' }}
            </button>

            <button
              type="button"
              :disabled="exportingPdf"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="exportPdf"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              {{ exportingPdf ? 'Exporting...' : 'Export PDF' }}
            </button>
          </div>
        </template>
      </PageHeader>

      <!-- Payslip Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ payslip.employee_name }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ payslip.department || '' }} {{ payslip.position ? `— ${payslip.position}` : '' }}
            </p>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <p class="text-sm text-gray-500 dark:text-gray-400">Period</p>
              <p class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ payslip.month_name || `Month ${payslip.month}` }} {{ payslip.year }}
              </p>
            </div>
            <StatusBadge :status="payslip.status" :variant-map="statusVariantMap" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Earnings Section -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Earnings</h3>
          <dl class="space-y-3">
            <div class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Basic Salary</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payslip.basic_salary) }}</dd>
            </div>
            <div v-if="payslip.housing_allowance" class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Housing Allowance</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payslip.housing_allowance) }}</dd>
            </div>
            <div v-if="payslip.transport_allowance" class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Transport Allowance</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payslip.transport_allowance) }}</dd>
            </div>
            <div v-if="payslip.medical_allowance" class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Medical Allowance</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payslip.medical_allowance) }}</dd>
            </div>
            <div v-if="payslip.other_allowances" class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Other Allowances</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payslip.other_allowances) }}</dd>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-gray-200 dark:border-gray-700">
              <dt class="text-sm font-semibold text-gray-700 dark:text-gray-300">Total Earnings</dt>
              <dd class="text-sm font-bold text-gray-900 dark:text-white">{{ formatAmount(payslip.gross_pay) }}</dd>
            </div>
          </dl>
        </div>

        <!-- Deductions Section -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Deductions</h3>
          <dl class="space-y-3">
            <div class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Tax</dt>
              <dd class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatAmount(payslip.tax) }}</dd>
            </div>
            <div class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Pension</dt>
              <dd class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatAmount(payslip.pension) }}</dd>
            </div>
            <div v-if="payslip.other_deductions" class="flex justify-between items-center">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Other Deductions</dt>
              <dd class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatAmount(payslip.other_deductions) }}</dd>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-gray-200 dark:border-gray-700">
              <dt class="text-sm font-semibold text-gray-700 dark:text-gray-300">Total Deductions</dt>
              <dd class="text-sm font-bold text-red-600 dark:text-red-400">{{ formatAmount(payslip.total_deductions) }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Net Pay - Highlighted -->
      <div class="mt-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800 p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <p class="text-lg font-semibold text-green-800 dark:text-green-300">Net Pay</p>
          <p class="text-3xl font-bold text-green-700 dark:text-green-400">
            {{ formatAmount(payslip.net_pay) }}
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
