/**
 * App.jsx — the root component, defines all routes.
 *
 * ROUTING STRUCTURE:
 *
 *   /                → redirect to /login
 *   /login           → AuthPage  (public — no token needed)
 *   /dashboard       → Dashboard (protected — needs login)
 *   /results/:dataId → ResultPage (protected)
 *   anything else    → redirect to /login
 *
 * HOW PROTECTED ROUTES WORK:
 * <Route element={<ProtectedRoute />}> creates a "layout route".
 * All child routes inside it first pass through ProtectedRoute,
 * which checks auth and renders <Navbar /> + <Outlet />.
 *
 * WHY AuthProvider WRAPS BrowserRouter:
 * AuthProvider must be an ancestor of everything, including the router,
 * so that even ProtectedRoute (which lives inside the router) can call useAuth().
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'
import ResultPage from './pages/ResultPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Redirect root to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Public — anyone can access */}
          <Route path="/login" element={<AuthPage />} />

          {/* Protected — ProtectedRoute checks auth for all children */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/results/:dataId" element={<ResultPage />} />
          </Route>

          {/* Catch-all — unknown URLs go to login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
