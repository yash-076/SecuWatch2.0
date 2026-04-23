import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const navigate = useNavigate()
  const { isAuthenticated, signup } = useAuth()

  const [form, setForm] = useState({
    email: '',
    password: '',
    organization_name: '',
    role: 'analyst',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleChange = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await signup(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Signup failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4">
      <div className="w-full max-w-lg card-base p-8 space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-soc-text">Create your SecuWatch account</h1>
          <p className="text-section-subtitle">Register and connect your organization</p>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-label mb-2">Organization Name</label>
            <input
              type="text"
              value={form.organization_name}
              onChange={handleChange('organization_name')}
              className="input-soc w-full"
              placeholder="Acme Security"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-label mb-2">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={handleChange('email')}
              className="input-soc w-full"
              placeholder="analyst@acme.com"
              required
            />
          </div>

          <div>
            <label className="block text-label mb-2">Role</label>
            <select value={form.role} onChange={handleChange('role')} className="input-soc w-full" required>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-label mb-2">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={handleChange('password')}
              className="input-soc w-full"
              placeholder="At least 8 characters"
              required
              minLength={8}
            />
          </div>

          {error && <p className="md:col-span-2 text-sm text-soc-critical">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="md:col-span-2 btn-primary w-full py-3 disabled:opacity-60"
          >
            {isSubmitting ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className="text-sm text-soc-secondary text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-soc-info hover:text-blue-400 font-medium">
            Login
          </Link>
        </p>
      </div>
    </div>
  )
}
