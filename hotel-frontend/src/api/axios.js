import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1/',
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const originalRequest = error.config

    // only attempt refresh once per request, on a 401, and only if we HAVE a refresh token
    if (error.response?.status === 401 && !originalRequest._retry && auth.refreshToken) {
      originalRequest._retry = true

      try {
        const response = await axios.post('http://localhost:8000/api/token/refresh/', {
          refresh: auth.refreshToken,
        })
        auth.accessToken = response.data.access
        localStorage.setItem('access_token', auth.accessToken)

        // your backend rotates refresh tokens too — SimpleJWT sends a new one back
        if (response.data.refresh) {
          auth.refreshToken = response.data.refresh
          localStorage.setItem('refresh_token', auth.refreshToken)
        }

        // retry the ORIGINAL request with the new token
        originalRequest.headers.Authorization = `Bearer ${auth.accessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        auth.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api