import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, AlertCircle, BarChart3, Wifi, Home, Shield } from 'lucide-react'

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(true)
  const location = useLocation()

  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: AlertCircle, label: 'Alerts', path: '/dashboard/alerts' },
    { icon: BarChart3, label: 'Analytics', path: '/dashboard/analytics' },
    { icon: Wifi, label: 'Devices', path: '/dashboard/devices' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <>
      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-screen bg-soc-sidebar border-r border-soc-border transition-smooth z-50 flex flex-col ${isOpen ? 'w-64' : 'w-20'}`}>
        {/* Header */}
        {/* Header */}
        <div className={`flex items-center h-20 border-b border-soc-border transition-smooth ${isOpen ? 'justify-between px-4' : 'justify-center px-0'}`}>
          {isOpen ? (
            <>
              <Link to="/" className="flex items-center gap-3 group cursor-pointer">
                <div className="w-9 h-9 bg-gradient-to-br from-soc-accent to-soc-accent-light rounded-lg flex items-center justify-center shadow-soc-glow group-hover:shadow-soc-glow-strong transition-all duration-300">
                  <Shield size={18} className="text-white" />
                </div>
                <span className="font-bold text-soc-text group-hover:opacity-80 transition-smooth">
                  Secu<span className="text-soc-accent">Watch</span>
                </span>
              </Link>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-soc-card rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
                title="Collapse Sidebar"
              >
                <X size={20} />
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsOpen(true)}
              className="p-2.5 hover:bg-soc-card rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
              title="Expand Sidebar"
            >
              <Menu size={20} />
            </button>
          )}
        </div>

        {/* Menu Items */}
        <nav className="flex-1 flex flex-col gap-2 p-4">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center transition-smooth rounded-lg ${
                isOpen ? 'px-4 py-3 gap-3 justify-start' : 'p-3 justify-center'
              } ${
                isActive(item.path)
                  ? 'bg-gradient-to-r from-soc-accent to-soc-accent-light text-white shadow-soc-glow'
                  : 'text-soc-secondary hover:bg-soc-card hover:text-soc-text'
              }`}
            >
              <item.icon size={20} className="flex-shrink-0" />
              {isOpen && <span className="font-medium text-sm">{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        {isOpen && (
          <div className="border-t border-soc-border p-4">
            <p className="text-xs text-soc-muted text-center font-medium">v2.0.0</p>
          </div>
        )}
      </div>

      {/* Spacer */}
      <div className={`transition-smooth ${isOpen ? 'w-64' : 'w-20'}`} />
    </>
  )
}
