import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Styles
import './assets/css/main.css'

// ECharts
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart, GaugeChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  DatasetComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

// Register ECharts modules
use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  DatasetComponent,
])

// ─── App Bootstrap ────────────────────────────────────────────
const app = createApp(App)

// Plugins
app.use(createPinia())
app.use(router)

// Global component registration
app.component('VChart', VChart)

// ─── Theme Initialisation ─────────────────────────────────────
function initTheme() {
  const stored = localStorage.getItem('theme')

  if (stored === 'light' || stored === 'dark') {
    document.documentElement.classList.toggle('dark', stored === 'dark')
  } else {
    // Respect system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', prefersDark)
    localStorage.setItem('theme', prefersDark ? 'dark' : 'light')
  }
}

initTheme()

// ─── Mount ────────────────────────────────────────────────────
app.mount('#app')
