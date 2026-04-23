import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, AlertCircle, BarChart3, Wifi, Home } from 'lucide-react'

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(true)
  const location = useLocation()

  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/' },
    { icon: AlertCircle, label: 'Alerts', path: '/alerts' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: Wifi, label: 'Devices', path: '/devices' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <>
      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-screen bg-soc-sidebar border-r border-soc-border transition-smooth z-50 flex flex-col ${isOpen ? 'w-64' : 'w-20'}`}>
        {/* Header */}
        <div className="flex items-center justify-between h-20 px-4 border-b border-soc-border">
          {isOpen && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-soc-info to-blue-600 rounded-lg flex items-center justify-center shadow-soc-md">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="font-bold text-soc-text">SecuWatch</span>
            </div>
          )}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-2 hover:bg-soc-card rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
          >
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 flex flex-col gap-2 p-4">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-smooth ${
                isActive(item.path)
                  ? 'bg-gradient-to-r from-soc-info to-blue-600 text-white shadow-soc-md'
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
            <p className="text-xs text-soc-muted text-center font-medium">v1.0.0</p>
          </div>
        )}
      </div>

      {/* Spacer */}
      <div className={`transition-smooth ${isOpen ? 'w-64' : 'w-20'}`} />
    </>
  )
}
