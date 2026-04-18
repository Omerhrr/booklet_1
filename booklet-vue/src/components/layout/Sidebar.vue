<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSidebarStore } from '@/stores/sidebar'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const sidebarStore = useSidebarStore()
const authStore = useAuthStore()

// ── Dropdown open states ──────────────────────────────────────────
const openSections = ref({
  crm: false,
  inventory: false,
  sales: false,
  purchases: false,
  accounting: false,
  hr: false,
  banking: false,
})

// Auto-open the section whose child is currently active
function initOpenSections() {
  const path = route.path
  if (path.startsWith('/crm')) openSections.value.crm = true
  if (path.startsWith('/inventory')) openSections.value.inventory = true
  if (path.startsWith('/sales')) openSections.value.sales = true
  if (path.startsWith('/purchases')) openSections.value.purchases = true
  if (path.startsWith('/accounting')) openSections.value.accounting = true
  if (path.startsWith('/hr')) openSections.value.hr = true
  if (path.startsWith('/banking')) openSections.value.banking = true
}
initOpenSections()

function toggleSection(section) {
  openSections.value[section] = !openSections.value[section]
}

// ── Permission & plan helpers ─────────────────────────────────────
function perm(p) {
  return authStore.hasPermission(p)
}

function anyPerm(perms) {
  return authStore.hasAnyPermission(perms)
}

function plan(feature) {
  return authStore.hasPlanFeature(feature)
}

// ── Active route detection ────────────────────────────────────────
function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function isSectionActive(paths) {
  return paths.some(p => route.path.startsWith(p))
}

// ── Navigation ────────────────────────────────────────────────────
function navigate(path) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.push('/auth/login')
}

// ── Tooltip for collapsed state ───────────────────────────────────
const tooltipTarget = ref(null)
const tooltipText = ref('')
const showTooltip = ref(false)

function onEnterTooltip(text) {
  if (!sidebarStore.isCollapsed) return
  tooltipText.value = text
  showTooltip.value = true
}

function onLeaveTooltip() {
  showTooltip.value = false
}
</script>

<template>
  <aside
    class="fixed left-0 top-0 h-full z-40 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all duration-300"
    :class="sidebarStore.isCollapsed ? 'w-16' : 'w-64'"
  >
    <!-- ── Logo Section ─────────────────────────────────────── -->
    <div class="flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
      <!-- "B" Icon -->
      <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
        <span class="text-white font-bold text-sm">B</span>
      </div>
      <!-- "Booklet" text -->
      <transition name="fade">
        <span
          v-if="!sidebarStore.isCollapsed"
          class="ml-3 text-lg font-bold text-gray-900 dark:text-white whitespace-nowrap"
        >
          Booklet
        </span>
      </transition>
    </div>

    <!-- ── Scrollable Menu Area ─────────────────────────────── -->
    <!-- <nav class="sidebar-nav flex-1 min-h-0 overflow-y-auto overflow-x-hidden py-4 px-2">
      <ul class="space-y-1"> -->

    <!-- <nav class="sidebar-nav flex-1 min-h-0 overflow-y-auto overflow-x-hidden py-4 px-2 
            scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700"> -->
      <nav class="flex-1 overflow-y-auto py-4 px-2 custom-scrollbar">
        <ul class="space-y-1">


        <!-- ════════════════════════════════════════════════════
             1. DASHBOARD — always visible
        ════════════════════════════════════════════════════ -->
        <li>
          <router-link
            to="/dashboard"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/dashboard')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Dashboard')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Pie Chart Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Dashboard</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             2. CRM (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['customers:view', 'vendors:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/crm'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('crm')"
            @mouseenter="onEnterTooltip('CRM')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Users Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">CRM</span>
            </transition>
            <!-- Chevron -->
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.crm }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <!-- CRM Sub-items (only when expanded) -->
          <transition name="slide-down">
            <ul v-if="openSections.crm && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('customers:view')">
                <router-link
                  to="/crm/customers"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/crm/customers') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Customers
                </router-link>
              </li>
              <li v-if="perm('vendors:view')">
                <router-link
                  to="/crm/vendors"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/crm/vendors') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  Vendors
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             3. INVENTORY (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['products:view', 'categories:view', 'stock:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/inventory'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('inventory')"
            @mouseenter="onEnterTooltip('Inventory')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Package Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">Inventory</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.inventory }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.inventory && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('products:view')">
                <router-link
                  to="/inventory/products"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/inventory/products') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  Products
                </router-link>
              </li>
              <li v-if="perm('categories:view')">
                <router-link
                  to="/inventory/categories"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/inventory/categories') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  Categories
                </router-link>
              </li>
              <li v-if="perm('stock:view')">
                <router-link
                  to="/inventory/stock-adjustments"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/inventory/stock-adjustments') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Stock Adjustments
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             4. SALES (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['invoices:view', 'credit_notes:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/sales'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('sales')"
            @mouseenter="onEnterTooltip('Sales')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Currency Dollar Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">Sales</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.sales }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.sales && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('invoices:view')">
                <router-link
                  to="/sales/invoices"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/sales/invoices') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Invoices
                </router-link>
              </li>
              <li v-if="perm('invoices:create')">
                <router-link
                  to="/sales/invoices/new"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/sales/invoices/new') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  New Invoice
                </router-link>
              </li>
              <li v-if="perm('credit_notes:view')">
                <router-link
                  to="/sales/credit-notes"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/sales/credit-notes') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                  </svg>
                  Credit Notes
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             5. PURCHASES (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['bills:view', 'debit_notes:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/purchases'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('purchases')"
            @mouseenter="onEnterTooltip('Purchases')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Shopping Cart Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">Purchases</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.purchases }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.purchases && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('bills:view')">
                <router-link
                  to="/purchases/bills"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/purchases/bills') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Bills
                </router-link>
              </li>
              <li v-if="perm('bills:create')">
                <router-link
                  to="/purchases/bills/new"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/purchases/bills/new') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  New Bill
                </router-link>
              </li>
              <li v-if="perm('debit_notes:view')">
                <router-link
                  to="/purchases/debit-notes"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/purchases/debit-notes') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  Debit Notes
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             6. EXPENSES (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('expenses:view')">
          <router-link
            to="/expenses"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/expenses')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Expenses')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Fire Icon (expense) -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Expenses</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             7. OTHER INCOME (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('other_income:view')">
          <router-link
            to="/other-incomes"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/other-incomes')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Other Income')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Trending Up Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Other Income</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             8. BUDGETS (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('budgets:view') && plan('budgets')">
          <router-link
            to="/budgets"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/budgets')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Budgets')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Calculator Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Budgets</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             9. FIXED ASSETS (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('accounting:view') && plan('fixed_assets')">
          <router-link
            to="/fixed-assets"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/fixed-assets')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Fixed Assets')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Building Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Fixed Assets</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             10. CASH BOOK (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('accounting:view')">
          <router-link
            to="/cashbook"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/cashbook')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Cash Book')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Book Open Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Cash Book</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             11. ACCOUNTING (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['accounts:view', 'journal:view', 'reports:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/accounting'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('accounting')"
            @mouseenter="onEnterTooltip('Accounting')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Scale/Balance Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">Accounting</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.accounting }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.accounting && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('accounts:view')">
                <router-link
                  to="/accounting/chart-of-accounts"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/chart-of-accounts') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  Chart of Accounts
                </router-link>
              </li>
              <li v-if="perm('journal:view')">
                <router-link
                  to="/accounting/journal"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/journal') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Journal
                </router-link>
              </li>
              <li v-if="perm('accounts:view')">
                <router-link
                  to="/accounting/ledger"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/ledger') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  General Ledger
                </router-link>
              </li>
              <li v-if="perm('reports:view')">
                <router-link
                  to="/accounting/balance-sheet"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/balance-sheet') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Balance Sheet
                </router-link>
              </li>
              <li v-if="perm('reports:view')">
                <router-link
                  to="/accounting/profit-loss"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/profit-loss') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  P&amp;L
                </router-link>
              </li>
              <li v-if="perm('reports:view')">
                <router-link
                  to="/accounting/trial-balance"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/accounting/trial-balance') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                  </svg>
                  Trial Balance
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             12. HR & PAYROLL (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['employees:view', 'payroll:view']) && plan('hr')">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/hr'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('hr')"
            @mouseenter="onEnterTooltip('HR & Payroll')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- User Group / Briefcase Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">HR &amp; Payroll</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.hr }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.hr && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('employees:view')">
                <router-link
                  to="/hr/employees"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/hr/employees') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Employees
                </router-link>
              </li>
              <li v-if="perm('payroll:view')">
                <router-link
                  to="/hr/payroll"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/hr/payroll') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Run Payroll
                </router-link>
              </li>
              <li v-if="perm('payroll:view')">
                <router-link
                  to="/hr/payslips"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/hr/payslips') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Payslips
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             13. BANKING (dropdown)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['banking:view', 'transfers:view', 'reconciliation:view'])">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isSectionActive(['/banking'])
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @click="!sidebarStore.isCollapsed && toggleSection('banking')"
            @mouseenter="onEnterTooltip('Banking')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Landmark / Bank Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11m16-11v11M8 14v3m4-3v3m4-3v3" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap flex-1 text-left">Banking</span>
            </transition>
            <transition name="fade">
              <svg
                v-if="!sidebarStore.isCollapsed"
                class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
                :class="{ 'rotate-90': openSections.banking }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </transition>
          </button>

          <transition name="slide-down">
            <ul v-if="openSections.banking && !sidebarStore.isCollapsed" class="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
              <li v-if="perm('banking:view')">
                <router-link
                  to="/banking/accounts"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/banking/accounts') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  Bank Accounts
                </router-link>
              </li>
              <li v-if="perm('transfers:view')">
                <router-link
                  to="/banking/transfers"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/banking/transfers') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  Transfers
                </router-link>
              </li>
              <li v-if="perm('reconciliation:view')">
                <router-link
                  to="/banking/reconciliation"
                  class="flex items-center px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="isActive('/banking/reconciliation') ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-gray-800' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                >
                  <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Reconciliation
                </router-link>
              </li>
            </ul>
          </transition>
        </li>

        <!-- ════════════════════════════════════════════════════
             14. REPORTS (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('reports:view')">
          <router-link
            to="/reports"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/reports')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Reports')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Chart Bar Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Reports</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             15. ANALYTICS HUB (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('reports:view') && plan('analytics')">
          <router-link
            to="/analytics"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/analytics')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Analytics Hub')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Sparkles / Analytics Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Analytics Hub</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             16. AI ASSISTANT (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('ai:use') && plan('ai')">
          <router-link
            to="/ai"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/ai')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('AI Assistant')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- CPU / Sparkle Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">AI Assistant</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             17. AGENTS (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('agents:use') && plan('agents')">
          <router-link
            to="/agents"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/agents')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Agents')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Robot Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Agents</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             18. SETTINGS (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="anyPerm(['users:view', 'roles:view', 'branches:view'])">
          <router-link
            to="/settings"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/settings')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Settings')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Cog Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Settings</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             19. AUDIT (single link)
        ════════════════════════════════════════════════════ -->
        <li v-if="perm('reports:view')">
          <router-link
            to="/audit"
            class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="[
              isActive('/audit')
                ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
              sidebarStore.isCollapsed ? 'justify-center' : ''
            ]"
            @mouseenter="onEnterTooltip('Audit')"
            @mouseleave="onLeaveTooltip"
          >
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Audit</span>
            </transition>
          </router-link>
        </li>

        <!-- ════════════════════════════════════════════════════
             20. LOGOUT — always visible
        ════════════════════════════════════════════════════ -->
        <li class="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700 mt-4">
          <button
            class="flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors text-gray-700 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-gray-800 hover:text-red-600 dark:hover:text-red-400"
            :class="sidebarStore.isCollapsed ? 'justify-center' : ''"
            @click="handleLogout"
            @mouseenter="onEnterTooltip('Logout')"
            @mouseleave="onLeaveTooltip"
          >
            <!-- Logout Icon -->
            <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <transition name="fade">
              <span v-if="!sidebarStore.isCollapsed" class="ml-3 whitespace-nowrap">Logout</span>
            </transition>
          </button>
        </li>

      </ul>
    </nav>

    <!-- ── Collapse Toggle Button ──────────────────────────── -->
    <div class="flex-shrink-0 border-t border-gray-200 dark:border-gray-800 p-2 hidden lg:block">
      <button
        class="flex items-center justify-center w-full p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        @click="sidebarStore.toggleCollapsed"
      >
        <svg
          class="w-5 h-5 transition-transform duration-200"
          :class="{ 'rotate-180': sidebarStore.isCollapsed }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- ── Tooltip ─────────────────────────────────────────── -->
    <transition name="tooltip">
      <div
        v-if="showTooltip"
        class="fixed z-50 left-16 bg-gray-900 dark:bg-gray-700 text-white text-xs px-2 py-1 rounded-md shadow-lg whitespace-nowrap pointer-events-none"
        style="transform: translateY(-50%);"
      >
        {{ tooltipText }}
      </div>
    </transition>
  </aside>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 500px;
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease;
}
.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}
</style>

<style>
/* Sidebar nav scrollable area — must be unscoped for scrollbar + .dark selector to work */
.sidebar-nav {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.4) transparent;
}
.sidebar-nav:hover {
  scrollbar-color: rgba(156, 163, 175, 0.7) transparent;
}
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}
.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-nav::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.4);
  border-radius: 3px;
}
.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7);
}
.dark .sidebar-nav {
  scrollbar-color: rgba(75, 85, 99, 0.5) transparent;
}
.dark .sidebar-nav:hover {
  scrollbar-color: rgba(75, 85, 99, 0.8) transparent;
}
.dark .sidebar-nav::-webkit-scrollbar-thumb {
  background-color: rgba(75, 85, 99, 0.5);
}
.dark .sidebar-nav::-webkit-scrollbar-thumb:hover {
  background-color: rgba(75, 85, 99, 0.8);
}
</style>
