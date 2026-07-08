import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, ArrowLeft } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, login } = useAuth()

  const redirectPath = location.state?.from || '/dashboard'

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
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
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4 bg-grid-pattern relative">
      {/* Glow */}
      <div className="hero-glow" style={{ top: '20%', left: '30%' }} />

      <div className="w-full max-w-md relative z-10">
        {/* Back to home */}
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-soc-secondary hover:text-soc-text transition-smooth mb-8">
          <ArrowLeft size={16} />
          Back to Home
        </Link>

        <div className="card-base p-8 space-y-6">
          {/* Brand */}
          <div className="text-center space-y-3">
            <div className="w-12 h-12 bg-gradient-to-br from-soc-accent to-soc-accent-light rounded-xl flex items-center justify-center mx-auto shadow-soc-glow">
              <Shield size={24} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-soc-text">Login to SecuWatch</h1>
            <p className="text-section-subtitle">Use your organization credentials</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-label mb-2">Email</label>
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
              className="w-full rounded-lg border border-soc-accent/30 px-4 py-3 text-soc-accent hover:bg-soc-accent/10 transition-smooth font-medium"
            >
              New user? Sign up
            </button>
          </form>

          <p className="text-sm text-soc-secondary text-center">
            New here?{' '}
            <Link to="/signup" className="text-soc-accent hover:text-soc-accent-light font-medium transition-smooth">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
