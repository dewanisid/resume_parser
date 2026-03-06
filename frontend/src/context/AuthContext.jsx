/**
 * Authentication Context
 *
 * WHAT IS REACT CONTEXT?
 * Context is React's built-in way to share data across many components without
 * "prop drilling" (passing the same prop through 5 layers of components).
 *
 * Think of it like a global variable, but one that React tracks — so when it
 * changes, every component that uses it re-renders automatically.
 *
 * HOW THIS WORKS:
 *  1. We create a Context object (AuthContext)
 *  2. AuthProvider is a component that wraps the whole app and "provides" the value
 *  3. useAuth() is a custom hook — any component calls it to get the auth state
 *
 * WHAT STATE IS MANAGED HERE:
 *  - user: null (not logged in) or { id, username, email, date_joined }
 *  - isLoading: true while we check if a saved token is still valid on startup
 *
 * WHAT FUNCTIONS ARE EXPOSED:
 *  - login(username, password) → returns { ok: true } or { ok: false, error }
 *  - register(username, email, password, password2) → same shape
 *  - logout() → clears tokens, sets user to null
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/client'

// Step 1: Create the context with a default value of null
// (null means "no provider found" — this should never happen in practice)
const AuthContext = createContext(null)

// ---------------------------------------------------------------------------
// AuthProvider — wraps the whole app
// ---------------------------------------------------------------------------
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // On first mount: check if a saved access token is still valid.
  // If so, load the user from the /me endpoint.
  // This makes refreshing the page preserve the logged-in state.
  //
  // WHAT IS useEffect?
  // useEffect runs code *after* the component renders.
  // The empty array [] means "run this only once, when the component first mounts".
  useEffect(() => {
    const token = localStorage.getItem('accessToken')
    if (!token) {
      setIsLoading(false)
      return
    }

    // A token exists — verify it by calling /me
    // The axios interceptor automatically attaches it as Authorization: Bearer <token>
    authApi.me()
      .then((userData) => {
        setUser(userData)
      })
      .catch(() => {
        // Token was invalid or expired and refresh failed — clean up
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  // -------------------------------------------------------------------------
  // login(username, password)
  // -------------------------------------------------------------------------
  async function login(username, password) {
    try {
      const data = await authApi.login({ username, password })
      // Store both tokens — access token is short-lived (1 hr), refresh is long (7 days)
      localStorage.setItem('accessToken', data.access)
      localStorage.setItem('refreshToken', data.refresh)

      // Fetch user profile (login only returns tokens, not user data)
      const userData = await authApi.me()
      setUser(userData)
      return { ok: true }
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        'Login failed. Please check your credentials.'
      return { ok: false, error: msg }
    }
  }

  // -------------------------------------------------------------------------
  // register(username, email, password, password2)
  // -------------------------------------------------------------------------
  async function register(username, email, password, password2) {
    try {
      // Register returns { user, access, refresh } — everything in one call
      const data = await authApi.register({ username, email, password, password2 })
      localStorage.setItem('accessToken', data.access)
      localStorage.setItem('refreshToken', data.refresh)
      setUser(data.user)
      return { ok: true }
    } catch (err) {
      // Django validation errors come back as { field: ["error message"] }
      // e.g. { username: ["A user with that username already exists."] }
      return { ok: false, errors: err.response?.data || {} }
    }
  }

  // -------------------------------------------------------------------------
  // logout()
  // -------------------------------------------------------------------------
  function logout() {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    setUser(null)
    // The caller is responsible for navigating to /login
  }

  const value = { user, isLoading, login, register, logout }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// ---------------------------------------------------------------------------
// useAuth — the custom hook components use to access auth state
// ---------------------------------------------------------------------------
// Instead of importing AuthContext and writing useContext(AuthContext) every time,
// components just write: const { user, login, logout } = useAuth()
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return ctx
}
