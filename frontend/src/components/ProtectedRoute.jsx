/**
 * ProtectedRoute
 *
 * This component acts as a gate in front of pages that require login.
 *
 * HOW IT WORKS:
 *  - If the user IS logged in → render the requested page (via <Outlet />)
 *  - If the user is NOT logged in → redirect them to /login
 *  - While we're still checking (isLoading) → show nothing to avoid a flash
 *
 * WHY isLoading MATTERS:
 * When the app first loads, AuthContext calls /auth/me to check if a saved
 * token is valid. This takes a fraction of a second. Without the isLoading
 * check, the user would briefly see the /login redirect before the check
 * completes — even if they ARE logged in. This is called a "flash of
 * unauthenticated content" and looks broken.
 *
 * WHAT IS <Outlet />?
 * In React Router, when you nest routes, <Outlet /> is where the child route
 * renders. So ProtectedRoute doesn't need to know *which* page to show —
 * it just says "if auth is valid, render whatever child route is active".
 * Both /dashboard and /results/:dataId are children of ProtectedRoute,
 * so they both automatically get the Navbar and the auth check.
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Navbar from './Navbar'

export default function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  // Still checking the token — render nothing to avoid a redirect flash
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  // Not logged in — send to login page
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Logged in — render the Navbar and then the actual page below it
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <Outlet />
    </div>
  )
}
