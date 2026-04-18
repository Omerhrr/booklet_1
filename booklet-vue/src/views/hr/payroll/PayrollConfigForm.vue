<script setup>
import { reactive, ref, watch } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'

const props = defineProps({
  config: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['save'])

const form = reactive({
  basic_salary: '',
  housing_allowance: '',
  transport_allowance: '',
  medical_allowance: '',
  other_allowances: '',
  tax_rate: '',
  pension_rate: '',
  other_deductions: '',
})

const errors = reactive({
  basic_salary: '',
  tax_rate: '',
  pension_rate: '',
})

// Watch for config changes to populate form
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig) {
      form.basic_salary = newConfig.basic_salary || ''
      form.housing_allowance = newConfig.housing_allowance || ''
      form.transport_allowance = newConfig.transport_allowance || ''
      form.medical_allowance = newConfig.medical_allowance || ''
      form.other_allowances = newConfig.other_allowances || ''
      form.tax_rate = newConfig.tax_rate || ''
      form.pension_rate = newConfig.pension_rate || ''
      form.other_deductions = newConfig.other_deductions || ''
    }
  },
  { immediate: true }
)

function validate() {
  let valid = true
  errors.basic_salary = ''
  errors.tax_rate = ''
  errors.pension_rate = ''

  if (!form.basic_salary || Number(form.basic_salary) <= 0) {
    errors.basic_salary = 'Basic salary is required'
    valid = false
  }
  if (form.tax_rate !== '' && (Number(form.tax_rate) < 0 || Number(form.tax_rate) > 100)) {
    errors.tax_rate = 'Tax rate must be between 0 and 100'
    valid = false
  }
  if (form.pension_rate !== '' && (Number(form.pension_rate) < 0 || Number(form.pension_rate) > 100)) {
    errors.pension_rate = 'Pension rate must be between 0 and 100'
    valid = false
  }

  return valid
}

function handleSubmit() {
  if (!validate()) return
  emit('save', {
    basic_salary: Number(form.basic_salary),
    housing_allowance: Number(form.housing_allowance) || 0,
    transport_allowance: Number(form.transport_allowance) || 0,
    medical_allowance: Number(form.medical_allowance) || 0,
    other_allowances: Number(form.other_allowances) || 0,
    tax_rate: Number(form.tax_rate) || 0,
    pension_rate: Number(form.pension_rate) || 0,
    other_deductions: Number(form.other_deductions) || 0,
  })
}
</script>

<template>
  <form class="space-y-6" @submit.prevent="handleSubmit">
    <div>
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Earnings</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <TextInput
          v-model="form.basic_salary"
          label="Basic Salary"
          name="basic_salary"
          type="number"
          placeholder="0.00"
          required
          :error="errors.basic_salary"
        />
        <TextInput
          v-model="form.housing_allowance"
          label="Housing Allowance"
          name="housing_allowance"
          type="number"
          placeholder="0.00"
        />
        <TextInput
          v-model="form.transport_allowance"
          label="Transport Allowance"
          name="transport_allowance"
          type="number"
          placeholder="0.00"
        />
        <TextInput
          v-model="form.medical_allowance"
          label="Medical Allowance"
          name="medical_allowance"
          type="number"
          placeholder="0.00"
        />
        <TextInput
          v-model="form.other_allowances"
          label="Other Allowances"
          name="other_allowances"
          type="number"
          placeholder="0.00"
        />
      </div>
    </div>

    <div>
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Deductions</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <TextInput
          v-model="form.tax_rate"
          label="Tax Rate (%)"
          name="tax_rate"
          type="number"
          placeholder="0"
          :error="errors.tax_rate"
          help-text="Percentage of gross pay"
        />
        <TextInput
          v-model="form.pension_rate"
          label="Pension Rate (%)"
          name="pension_rate"
          type="number"
          placeholder="0"
          :error="errors.pension_rate"
          help-text="Percentage of basic salary"
        />
        <TextInput
          v-model="form.other_deductions"
          label="Other Deductions"
          name="other_deductions"
          type="number"
          placeholder="0.00"
        />
      </div>
    </div>

    <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        type="submit"
        :disabled="loading"
        class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <LoadingSpinner v-if="loading" size="sm" />
        {{ loading ? 'Saving...' : 'Save Configuration' }}
      </button>
    </div>
  </form>
</template>
