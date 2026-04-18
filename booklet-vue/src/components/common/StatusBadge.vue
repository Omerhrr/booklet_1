<script setup>
import { computed } from 'vue'
import Badge from './Badge.vue'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
  variantMap: {
    type: Object,
    default: null,
  },
})

const defaultVariantMap = {
  active: 'success',
  inactive: 'danger',
  paid: 'success',
  unpaid: 'warning',
  pending: 'info',
  draft: 'default',
  overdue: 'danger',
  cancelled: 'danger',
  partial: 'warning',
  approved: 'success',
  posted: 'success',
  open: 'info',
}

const variant = computed(() => {
  const map = props.variantMap || defaultVariantMap
  return map[props.status] || 'default'
})

const formattedStatus = computed(() => {
  if (!props.status) return ''
  return props.status.charAt(0).toUpperCase() + props.status.slice(1).replace(/_/g, ' ')
})
</script>

<template>
  <Badge :text="formattedStatus" :variant="variant" size="sm" />
</template>
