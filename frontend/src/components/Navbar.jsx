/**
 * Navbar — top navigation bar shown on all protected pages.
 *
 * Shows:
 *  - App name (links to /dashboard)
 *  - Logged-in username
 *  - Logout button
 *
 * CONCEPTS USED:
 *  - useAuth() — gets the user object and logout function from context
 *  - useNavigate() — React Router hook that lets us navigate programmatically
 *    (i.e. after clicking logout, redirect to /login in code, not via a link)
 *  - Tailwind classes — e.g. "flex items-center justify-between px-6 py-4 border-b"
 *    means: flexbox row, vertically centred, space between items, padding, bottom border
 */

import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button } from '@/components/ui/button'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav className="border-b bg-background px-6 py-3 flex items-center justify-between">
      {/* Left side — app name */}
      <Link to="/dashboard" className="font-semibold text-lg tracking-tight">
        Resume Parser
      </Link>

      {/* Right side — username + logout */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {user?.username}
        </span>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Logout
        </Button>
      </div>
    </nav>
  )
}
