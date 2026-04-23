import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, login } = useAuth()

  const redirectPath = location.state?.from || '/'

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('')
    setIsSubmitting(true)

    try {
      await login({ email: username, password })
      navigate(redirectPath, { replace: true })
    } catch (err) {
      setError(err.message || 'Login failed. Check credentials.')
      setPassword('')
    }
    finally {
      setIsSubmitting(false)
    }
  };
  const newUserHandler = () => {
    navigate('/signup')
  }
  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md card-base p-8 space-y-6">
            <div className="text-center space-y-2">
              <h1 className="text-2xl font-bold text-soc-text">Login to Your Account</h1>
              <p className="text-section-subtitle">Use your organization credentials</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-label mb-2">Username</label>
                <input
                  className="input-soc w-full"
                  placeholder="admin@company.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  type="email"
                  required
                />
              </div>

              <div>
                <label className="block text-label mb-2">Password</label>
                <input
                  className="input-soc w-full"
                  placeholder="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {error && <p className="text-sm text-soc-critical">{error}</p>}

              <button
                className="btn-primary w-full py-3 disabled:opacity-60"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Logging in...' : 'Login'}
              </button>

              <button
                type="button"
                onClick={newUserHandler}
                className="w-full rounded-md border border-soc-info/30 px-4 py-3 text-soc-info hover:bg-soc-info/10"
              >
                New user? Sign up
              </button>
            </form>

            <p className="text-sm text-soc-secondary text-center">
              New here?{' '}
              <Link to="/signup" className="text-soc-info hover:text-blue-400 font-medium">
                Create an account
              </Link>
            </p>
          </div>
    </div>
  )
}
