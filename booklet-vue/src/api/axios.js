import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    const branchId = localStorage.getItem('selected_branch_id')
    if (branchId) {
      config.headers['X-Branch-Id'] = branchId
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      const { status, data } = error.response

      if (status === 401) {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken && !error.config._retry) {
          error.config._retry = true
          try {
            const response = await axios.post(
              (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1') + '/auth/refresh',
              { refresh_token: refreshToken }
            )
            const newToken = response.data.access_token
            localStorage.setItem('access_token', newToken)
            error.config.headers.Authorization = `Bearer ${newToken}`
            return api(error.config)
          } catch (refreshError) {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('selected_branch_id')
            localStorage.removeItem('selected_branch_name')
            localStorage.removeItem('branch_currency')
            localStorage.removeItem('permissions')
            localStorage.removeItem('is_superuser')
            localStorage.removeItem('plan_limits')
            if (window.location.pathname !== '/auth/login') {
              window.location.href = '/auth/login'
            }
          }
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('selected_branch_id')
          localStorage.removeItem('selected_branch_name')
          localStorage.removeItem('branch_currency')
          localStorage.removeItem('permissions')
          localStorage.removeItem('is_superuser')
          localStorage.removeItem('plan_limits')
          if (window.location.pathname !== '/auth/login') {
            window.location.href = '/auth/login'
          }
        }
      }

      if (status === 403) {
        const message =
          data?.detail || data?.message || 'You do not have permission to perform this action.'
        showToast(message, 'error')
      }

      if (status === 500) {
        const message =
          data?.detail || data?.message || 'An internal server error occurred. Please try again later.'
        showToast(message, 'error')
      }
    }

    return Promise.reject(error)
  }
)

// Lightweight toast helper (avoids circular dependency with Pinia store)
function showToast(message, type = 'error') {
  // Try to use the toast store if available; otherwise fall back to a native alert
  try {
    // Dynamic import to avoid circular deps
    import('@/stores/toast').then(({ useToastStore }) => {
      const toastStore = useToastStore()
      toastStore.show(message, type)
    })
  } catch {
    // Fallback for environments where Pinia isn't ready yet
    console.error(`[${type}] ${message}`)
  }
}

export default api
