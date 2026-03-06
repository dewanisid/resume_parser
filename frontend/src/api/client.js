/**
 * API client — the single source of truth for all HTTP calls.
 *
 * WHAT IS AXIOS?
 * Axios is an HTTP library (similar to Python's `requests`). We could use
 * the browser's built-in fetch(), but axios gives us:
 *  - Automatic JSON parsing (no need for response.json())
 *  - Interceptors (middleware that runs on every request/response)
 *  - Better error objects with response data attached
 *
 * HOW THIS FILE IS ORGANISED:
 *  1. Create the axios instance with default settings
 *  2. Request interceptor  — attaches the JWT token to every outgoing request
 *  3. Response interceptor — catches 401 errors and tries to refresh the token
 *  4. authApi   — functions for register, login, /me
 *  5. resumeApi — functions for upload, job status, list, data, delete
 */

import axios from 'axios'

// ---------------------------------------------------------------------------
// 1. Create the axios instance
// ---------------------------------------------------------------------------
// baseURL: empty string means all paths are relative ('/api/v1/...')
// Vite's dev proxy then forwards those to http://localhost:8000
// In production, VITE_API_BASE_URL would be 'https://api.yoursite.com'
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000, // 30 seconds — long because PDF parsing can be slow
})

// ---------------------------------------------------------------------------
// 2. Request interceptor — attach Authorization header
// ---------------------------------------------------------------------------
// This runs BEFORE every single request is sent.
// It reads the stored access token from localStorage and adds it as a header.
// Without this, we'd have to manually add the header in every API call.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------------------
// 3. Response interceptor — handle 401 with token refresh
// ---------------------------------------------------------------------------
// This runs AFTER every response comes back.
// When Django returns 401 (Unauthorized), it usually means the access token
// expired (they last 1 hour). We automatically:
//  a) Call /auth/refresh with the refresh token (lasts 7 days)
//  b) Get a new access token
//  c) Retry the original failed request with the new token
//  d) If the refresh also fails, clear storage and redirect to /login

// These two variables prevent a race condition where multiple requests all
// expire at the same moment and each try to refresh independently.
// Instead, only the first one refreshes; the others wait in the queue.
let isRefreshing = false
let failedQueue = [] // [{resolve, reject}]

function processQueue(error, token = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  // Success (2xx): just pass the response through unchanged
  (response) => response,

  // Error: check if it's a 401 we should try to recover from
  async (error) => {
    const originalRequest = error.config

    const is401 = error.response?.status === 401
    const alreadyRetried = originalRequest._retry
    const isRefreshEndpoint = originalRequest.url?.includes('/auth/refresh')

    if (is401 && !alreadyRetried && !isRefreshEndpoint) {
      if (isRefreshing) {
        // Another request is already refreshing — park this one in the queue
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) {
        // No refresh token at all — user must log in again
        localStorage.removeItem('accessToken')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // Use a plain axios call (not apiClient) to avoid triggering this
        // interceptor recursively
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh: refreshToken,
        })
        const newToken = data.access
        localStorage.setItem('accessToken', newToken)
        apiClient.defaults.headers.common.Authorization = `Bearer ${newToken}`
        processQueue(null, newToken) // wake up all queued requests
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalRequest) // retry the original request
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// ---------------------------------------------------------------------------
// 4. Auth API functions
// ---------------------------------------------------------------------------
// Every function here returns the `data` part of the axios response directly.
// The caller gets the actual JSON payload — no need to do response.data.
export const authApi = {
  /**
   * Register a new user.
   * payload = { username, email, password, password2 }
   * Returns { user, access, refresh }
   */
  register: (payload) =>
    apiClient.post('/api/v1/auth/register', payload).then((r) => r.data),

  /**
   * Log in with credentials.
   * payload = { username, password }  ← Django's simplejwt expects username, not email
   * Returns { access, refresh }
   */
  login: (payload) =>
    apiClient.post('/api/v1/auth/login', payload).then((r) => r.data),

  /**
   * Get the currently authenticated user's profile.
   * Returns { id, username, email, date_joined }
   */
  me: () =>
    apiClient.get('/api/v1/auth/me').then((r) => r.data),
}

// ---------------------------------------------------------------------------
// 5. Resume API functions
// ---------------------------------------------------------------------------
export const resumeApi = {
  /**
   * Upload a PDF file for parsing.
   * file = a File object from an <input type="file"> or drag-and-drop
   * Returns { job_id, status, message, estimated_time_seconds }
   */
  upload: (file) => {
    // FormData is the browser's way of sending a file in a multipart request
    // It's the same as `curl -F "file=@resume.pdf"`
    const form = new FormData()
    form.append('file', file)
    return apiClient
      .post('/api/v1/resumes/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },

  /**
   * Get the current status of a parse job.
   * Returns { id, user_id, status, original_filename, ... }
   * When completed, also includes: result: { data_id, confidence_score }
   */
  getJob: (jobId) =>
    apiClient.get(`/api/v1/resumes/jobs/${jobId}`).then((r) => r.data),

  /**
   * Get a paginated list of the user's jobs, newest first.
   * Returns { count, next, previous, results: [...jobs] }
   */
  listJobs: (page = 1) =>
    apiClient.get('/api/v1/resumes/list', { params: { page } }).then((r) => r.data),

  /**
   * Get the full parsed resume data.
   * Returns { id, job_id, validated_data: { contact, summary, experience, ... }, ... }
   * NOTE: the actual resume JSON lives at validated_data, not at the top level.
   */
  getData: (dataId) =>
    apiClient.get(`/api/v1/resumes/data/${dataId}`).then((r) => r.data),

  /**
   * Delete a job and its uploaded PDF.
   * Returns nothing (204 No Content)
   */
  deleteJob: (jobId) =>
    apiClient.delete(`/api/v1/resumes/jobs/${jobId}/delete`).then((r) => r.data),
}

export default apiClient
