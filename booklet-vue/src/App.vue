<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Toast from '@/components/common/Toast.vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appReady = ref(false)

const isAuthRoute = computed(() => {
  return route.path.startsWith('/auth')
})

onMounted(async () => {
  await router.isReady()
  await authStore.initialize()
  appReady.value = true
})
</script>

<template>
  <div v-if="!appReady" class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
    <div class="animate-spin h-8 w-8 rounded-full border-4 border-blue-200 border-t-blue-600"></div>
  </div>
  <template v-else>
    <Toast />
    <AppLayout v-if="!isAuthRoute" />
    <router-view v-else />
  </template>
</template>
