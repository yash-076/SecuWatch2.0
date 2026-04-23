import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  clearAuthTokens,
  getCurrentUser,
  hasAccessToken,
  loginUser,
  logoutUser,
  registerUser,
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    const bootstrapAuth = async () => {
      if (!hasAccessToken()) {
        if (isMounted) setIsLoading(false)
        return
      }

      try {
        const profile = await getCurrentUser()
        if (isMounted) setUser(profile)
      } catch (_error) {
        clearAuthTokens()
        if (isMounted) setUser(null)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    bootstrapAuth()

    return () => {
      isMounted = false
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      async login({ email, password }) {
        await loginUser({ email, password })
        const profile = await getCurrentUser()
        setUser(profile)
      },
      async signup({ email, password, organization_name, role }) {
        await registerUser({ email, password, organization_name, role })
        await loginUser({ email, password })
        const profile = await getCurrentUser()
        setUser(profile)
      },
      async logout() {
        await logoutUser()
        setUser(null)
      },
    }),
    [user, isLoading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
