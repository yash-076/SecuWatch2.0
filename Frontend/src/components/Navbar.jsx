import { Bell, LogOut, Search, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <nav className="h-20 bg-soc-sidebar border-b border-soc-border flex items-center justify-between px-8 shadow-soc-md">
      {/* Search Bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-soc-muted" />
          <input
            type="text"
            placeholder="Search alerts, devices..."
            className="w-full pl-12 pr-4 py-2.5 bg-soc-card border border-soc-border rounded-lg text-soc-text placeholder:text-soc-muted focus:outline-none focus:border-soc-info focus:ring-1 focus:ring-soc-info transition-smooth"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-8 ml-12">
        {/* Notifications */}
        <div className="relative cursor-pointer hover:opacity-80 transition-smooth">
          <Bell size={20} className="text-soc-secondary hover:text-soc-text transition-smooth" />
          <span className="absolute -top-2 -right-2 bg-soc-critical text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold animate-pulse-subtle">
            3
          </span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="p-2 hover:bg-soc-card rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
          title="Logout"
        >
          <LogOut size={20} />
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-8 border-l border-soc-border hover:opacity-80 transition-smooth cursor-pointer">
          <div className="w-10 h-10 bg-gradient-to-br from-soc-info to-blue-600 rounded-lg flex items-center justify-center shadow-soc-md">
            <User size={20} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-soc-text">{user?.email || 'User'}</p>
            <p className="text-xs text-soc-muted capitalize">{user?.role || 'analyst'}</p>
          </div>
        </div>
      </div>
    </nav>
  )
}
