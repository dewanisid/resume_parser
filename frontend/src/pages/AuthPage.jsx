/**
 * AuthPage — Login and Register forms.
 *
 * CONCEPTS USED:
 *  - useState: tracks form field values and error messages
 *  - Tabs (shadcn): lets users switch between Login and Register without a page reload
 *  - useNavigate: after successful auth, redirect to /dashboard in code
 *  - useAuth: calls login() or register() from AuthContext
 *
 * FORM STATE PATTERN:
 * Each input is "controlled" — its value is stored in React state and the
 * input displays that state value. When the user types, onChange updates the
 * state, which re-renders the input with the new value. This keeps React in
 * control of the form at all times.
 *
 * WHY TWO SEPARATE STATE OBJECTS?
 * Login only needs username + password.
 * Register also needs email + password2 (confirmation).
 * Keeping them separate means switching tabs resets only the relevant fields.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function AuthPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  // ---------------------------------------------------------------------------
  // Login form state
  // ---------------------------------------------------------------------------
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  async function handleLogin(e) {
    e.preventDefault() // prevent the browser's default form submission (page reload)
    setLoginError('')
    setLoginLoading(true)

    const result = await login(loginForm.username, loginForm.password)

    setLoginLoading(false)
    if (result.ok) {
      navigate('/dashboard')
    } else {
      setLoginError(result.error)
    }
  }

  // ---------------------------------------------------------------------------
  // Register form state
  // ---------------------------------------------------------------------------
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
  })
  const [registerErrors, setRegisterErrors] = useState({})
  const [registerLoading, setRegisterLoading] = useState(false)

  async function handleRegister(e) {
    e.preventDefault()
    setRegisterErrors({})
    setRegisterLoading(true)

    const result = await register(
      registerForm.username,
      registerForm.email,
      registerForm.password,
      registerForm.password2
    )

    setRegisterLoading(false)
    if (result.ok) {
      navigate('/dashboard')
    } else {
      setRegisterErrors(result.errors)
    }
  }

  // Helper: extract the first error message for a field from Django's error format
  // Django returns: { username: ["A user with that username already exists."] }
  function fieldError(errors, field) {
    const msgs = errors?.[field]
    if (!msgs) return null
    return Array.isArray(msgs) ? msgs[0] : msgs
  }

  // Non-field errors (e.g. password mismatch returned as { password: [...] })
  const generalRegisterError =
    fieldError(registerErrors, 'non_field_errors') ||
    fieldError(registerErrors, 'detail')

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        {/* App title above the card */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold">Resume Parser</h1>
          <p className="mt-2 text-muted-foreground">
            Upload your PDF resume and get structured data in seconds.
          </p>
        </div>

        {/* Tabs switch between Login and Register */}
        <Tabs defaultValue="login">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="register">Register</TabsTrigger>
          </TabsList>

          {/* ----------------------------------------------------------------
              LOGIN TAB
          ---------------------------------------------------------------- */}
          <TabsContent value="login">
            <Card>
              <CardHeader>
                <CardTitle>Welcome back</CardTitle>
                <CardDescription>Sign in to your account</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-1">
                    <Label htmlFor="login-username">Username</Label>
                    <Input
                      id="login-username"
                      type="text"
                      placeholder="your_username"
                      value={loginForm.username}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, username: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="login-password">Password</Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="••••••••"
                      value={loginForm.password}
                      onChange={(e) =>
                        setLoginForm({ ...loginForm, password: e.target.value })
                      }
                      required
                    />
                  </div>

                  {/* Error message from the API */}
                  {loginError && (
                    <p className="text-sm text-destructive">{loginError}</p>
                  )}

                  <Button type="submit" className="w-full" disabled={loginLoading}>
                    {loginLoading ? 'Signing in...' : 'Sign in'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ----------------------------------------------------------------
              REGISTER TAB
          ---------------------------------------------------------------- */}
          <TabsContent value="register">
            <Card>
              <CardHeader>
                <CardTitle>Create an account</CardTitle>
                <CardDescription>Start parsing resumes for free</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-1">
                    <Label htmlFor="reg-username">Username</Label>
                    <Input
                      id="reg-username"
                      type="text"
                      placeholder="your_username"
                      value={registerForm.username}
                      onChange={(e) =>
                        setRegisterForm({ ...registerForm, username: e.target.value })
                      }
                      required
                    />
                    {fieldError(registerErrors, 'username') && (
                      <p className="text-xs text-destructive">
                        {fieldError(registerErrors, 'username')}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="reg-email">Email</Label>
                    <Input
                      id="reg-email"
                      type="email"
                      placeholder="you@example.com"
                      value={registerForm.email}
                      onChange={(e) =>
                        setRegisterForm({ ...registerForm, email: e.target.value })
                      }
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="reg-password">Password</Label>
                    <Input
                      id="reg-password"
                      type="password"
                      placeholder="Min. 8 characters"
                      value={registerForm.password}
                      onChange={(e) =>
                        setRegisterForm({ ...registerForm, password: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="reg-password2">Confirm password</Label>
                    <Input
                      id="reg-password2"
                      type="password"
                      placeholder="••••••••"
                      value={registerForm.password2}
                      onChange={(e) =>
                        setRegisterForm({ ...registerForm, password2: e.target.value })
                      }
                      required
                    />
                    {fieldError(registerErrors, 'password') && (
                      <p className="text-xs text-destructive">
                        {fieldError(registerErrors, 'password')}
                      </p>
                    )}
                  </div>

                  {generalRegisterError && (
                    <p className="text-sm text-destructive">{generalRegisterError}</p>
                  )}

                  <Button type="submit" className="w-full" disabled={registerLoading}>
                    {registerLoading ? 'Creating account...' : 'Create account'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
