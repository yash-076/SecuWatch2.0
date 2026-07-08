import { useEffect, useMemo, useRef, useState } from 'react'
import { Bell, LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { formatTimeAgo, getAlerts, mapSeverityLabel } from '../services/api'

const NOTIFICATION_REFRESH_MS = 20000

const mapAlertToNotification = (alert) => ({
  id: alert.id,
  title: alert.type || 'High Severity Alert',
  message: alert.description || `Device ${alert.device_id} triggered a high alert`,
  createdAt: alert.created_at,
  severity: mapSeverityLabel(alert.severity),
})

export default function Navbar() {
  const { user, logout } = useAuth()
  const [isNotificationOpen, setIsNotificationOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [lastSeenAt, setLastSeenAt] = useState(Date.now())
  const notificationRef = useRef(null)

  const unreadCount = useMemo(() => {
    return notifications.filter((notification) => {
      const timestamp = new Date(notification.createdAt).getTime()
      return !Number.isNaN(timestamp) && timestamp > lastSeenAt
    }).length
  }, [lastSeenAt, notifications])

  useEffect(() => {
    let isMounted = true

    const loadHighSeverityAlerts = async () => {
      try {
        const response = await getAlerts({ page: 1, limit: 20, severity: 'high' })
        if (!isMounted) return
        const highAlerts = Array.isArray(response?.alerts) ? response.alerts : []
        setNotifications(highAlerts.map(mapAlertToNotification))
      } catch (_error) {
        if (isMounted) {
          setNotifications([])
        }
      }
    }

    loadHighSeverityAlerts()
    const intervalId = window.setInterval(loadHighSeverityAlerts, NOTIFICATION_REFRESH_MS)

    return () => {
      isMounted = false
      window.clearInterval(intervalId)
    }
  }, [])

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setIsNotificationOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handleLogout = async () => {
    await logout()
  }

  const handleNotificationToggle = () => {
    setIsNotificationOpen((current) => {
      const nextState = !current
      if (nextState) {
        setLastSeenAt(Date.now())
      }
      return nextState
    })
  }

  return (
    <nav className="h-20 bg-soc-sidebar border-b border-soc-border flex items-center justify-end px-8 shadow-soc-md">
      {/* Right Actions */}
      <div className="flex items-center gap-8">
        {/* Notifications */}
        <div ref={notificationRef} className="relative">
          <button
            onClick={handleNotificationToggle}
            className="relative cursor-pointer hover:opacity-80 transition-smooth"
            title="Notifications"
          >
            <Bell size={20} className="text-soc-secondary hover:text-soc-text transition-smooth" />
            {unreadCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-soc-critical text-white text-xs rounded-full min-w-[20px] h-5 px-1 flex items-center justify-center font-bold animate-pulse-subtle">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {isNotificationOpen && (
            <div className="absolute right-0 mt-3 w-96 max-w-[90vw] bg-soc-card border border-soc-border rounded-xl shadow-soc-overlay z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-soc-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-soc-text">High Alert Notifications</h3>
                <span className="text-xs text-soc-muted">{notifications.length} total</span>
              </div>

              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 && (
                  <p className="px-4 py-6 text-sm text-soc-muted">No high alerts at the moment.</p>
                )}

                {notifications.map((notification) => (
                  <div key={notification.id} className="px-4 py-3 border-b border-soc-border last:border-b-0 hover:bg-soc-bg transition-smooth">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-soc-text truncate">{notification.title}</p>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500 bg-opacity-15 text-orange-400 flex-shrink-0">
                        {notification.severity}
                      </span>
                    </div>
                    <p className="text-xs text-soc-secondary mt-1 line-clamp-2">{notification.message}</p>
                    <p className="text-xs text-soc-muted mt-2">{formatTimeAgo(notification.createdAt)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
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
          <div className="w-10 h-10 bg-gradient-to-br from-soc-accent to-soc-accent-light rounded-lg flex items-center justify-center shadow-soc-glow">
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
