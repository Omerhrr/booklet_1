<script setup>
import { ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'

const categories = ref([
  {
    title: 'Sales Reports',
    description: 'Track invoices, revenue, customer payments and sales trends.',
    icon: 'M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z',
    route: { name: 'SalesReport' },
    color: 'emerald',
  },
  {
    title: 'Purchase Reports',
    description: 'Monitor bills, vendor payments and procurement patterns.',
    icon: 'M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-5.98.572M7.5 14.25a3 3 0 01-5.98-.572m11.98 0a3 3 0 10-5.98.572M7.5 14.25a3 3 0 11-5.98-.572M18 6.75a3 3 0 013 3v.75m-3-3.75H5.25m13.5 0h.375a1.125 1.125 0 011.125 1.125v.75m-15 0h15m-15 0H5.25m15 0A3.375 3.375 0 0121 12.875m-15 0h.375a3.375 3.375 0 013.375 3.375v.75',
    route: { name: 'PurchasesReport' },
    color: 'violet',
  },
  {
    title: 'Expense Reports',
    description: 'Analyze spending by category, date and payment method.',
    icon: 'M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z',
    route: { name: 'ExpensesReport' },
    color: 'amber',
  },
  {
    title: 'Inventory Reports',
    description: 'Review stock levels, product values and low-stock alerts.',
    icon: 'M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z',
    route: { name: 'InventoryReport' },
    color: 'cyan',
  },
  {
    title: 'Aging Reports',
    description: 'View receivables and payables aging by time buckets.',
    icon: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z',
    route: { name: 'AgingReport' },
    color: 'rose',
  },
  {
    title: 'Trial Balance',
    description: 'Verify debit and credit balances across all accounts.',
    icon: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
    route: { name: 'TrialBalanceReport' },
    color: 'purple',
  },
  {
    title: 'VAT Reports',
    description: 'Track output and input VAT, net payable and filing status.',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    route: { name: 'VatReport' },
    color: 'teal',
  },
  {
    title: 'Accounting Reports',
    description: 'Balance Sheet, Profit & Loss, and General Ledger reports.',
    icon: 'M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25V13.5zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25V18zm2.498-6.75h.007v.008h-.007v-.008zm0 2.25h.007v.008h-.007V13.5zm0 2.25h.007v.008h-.007v-.008zm0 2.25h.007v.008h-.007V18zm2.504-6.75h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V13.5zm0 2.25h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V18zm2.498-6.75h.008v.008h-.008v-.008zM15.75 13.5h.008v.008h-.008V13.5zM3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125zm0 4.5h17.25c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125H3.375a1.125 1.125 0 01-1.125-1.125v-1.5c0-.621.504-1.125 1.125-1.125z',
    route: '/accounting',
    color: 'orange',
    subItems: [
      { label: 'Balance Sheet', route: '/accounting/balance-sheet' },
      { label: 'Profit & Loss', route: '/accounting/profit-loss' },
      { label: 'General Ledger', route: '/accounting/general-ledger' },
    ],
  },
])

const colorMap = {
  emerald: {
    icon: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400',
    hover: 'hover:border-emerald-300 dark:hover:border-emerald-700',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  violet: {
    icon: 'bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400',
    hover: 'hover:border-violet-300 dark:hover:border-violet-700',
    border: 'border-violet-200 dark:border-violet-800',
  },
  amber: {
    icon: 'bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400',
    hover: 'hover:border-amber-300 dark:hover:border-amber-700',
    border: 'border-amber-200 dark:border-amber-800',
  },
  cyan: {
    icon: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/40 dark:text-cyan-400',
    hover: 'hover:border-cyan-300 dark:hover:border-cyan-700',
    border: 'border-cyan-200 dark:border-cyan-800',
  },
  rose: {
    icon: 'bg-rose-100 text-rose-600 dark:bg-rose-900/40 dark:text-rose-400',
    hover: 'hover:border-rose-300 dark:hover:border-rose-700',
    border: 'border-rose-200 dark:border-rose-800',
  },
  purple: {
    icon: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400',
    hover: 'hover:border-purple-300 dark:hover:border-purple-700',
    border: 'border-purple-200 dark:border-purple-800',
  },
  teal: {
    icon: 'bg-teal-100 text-teal-600 dark:bg-teal-900/40 dark:text-teal-400',
    hover: 'hover:border-teal-300 dark:hover:border-teal-700',
    border: 'border-teal-200 dark:border-teal-800',
  },
  orange: {
    icon: 'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400',
    hover: 'hover:border-orange-300 dark:hover:border-orange-700',
    border: 'border-orange-200 dark:border-orange-800',
  },
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Reports"
      subtitle="Generate and export business reports"
    />

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <component
        :is="category.subItems ? 'div' : 'router-link'"
        v-for="category in categories"
        :key="category.title"
        :to="category.subItems ? undefined : category.route"
        :class="[
          'group relative flex flex-col p-6 rounded-xl border bg-white dark:bg-gray-800 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg cursor-pointer',
          colorMap[category.color]?.border || 'border-gray-200 dark:border-gray-700',
          colorMap[category.color]?.hover || 'hover:border-gray-300 dark:hover:border-gray-600',
        ]"
      >
        <!-- Icon -->
        <div
          :class="[
            'w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110',
            colorMap[category.color]?.icon || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
          ]"
        >
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" :d="category.icon" />
          </svg>
        </div>

        <!-- Content -->
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1">
          {{ category.title }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-4">
          {{ category.description }}
        </p>

        <!-- Sub-items or arrow -->
        <div v-if="category.subItems" class="mt-auto space-y-1.5">
          <router-link
            v-for="sub in category.subItems"
            :key="sub.label"
            :to="sub.route"
            class="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            @click.stop
          >
            <span class="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600" />
            {{ sub.label }}
          </router-link>
        </div>
        <div v-else class="mt-auto flex items-center gap-1 text-sm font-medium text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
          <span>Open</span>
          <svg class="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </div>
      </component>
    </div>
  </div>
</template>
