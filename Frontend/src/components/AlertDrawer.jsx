import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { getUsers, assignAlert, assignAlertToMe, updateAlertStatus, getCurrentUser } from '../services/api'

const getSeverityColor = (severity) => {
  const colors = {
    Critical: '#ef4444',
    High: '#f97316',
    Medium: '#f59e0b',
    Low: '#22c55e',
    Info: '#e63946',
  }
  return colors[severity] || '#f0f0f0'
}

export default function AlertDrawer({ alert, onClose, onUpdate }) {
  const [users, setUsers] = useState([])
  const [currentUser, setCurrentUser] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!alert) return
    let isMounted = true

    getUsers()
      .then((data) => {
        if (isMounted) setUsers(Array.isArray(data) ? data : [])
      })
      .catch((err) => console.error('Failed to fetch organization users:', err))

    getCurrentUser()
      .then((user) => {
        if (isMounted) setCurrentUser(user)
      })
      .catch((err) => console.error('Failed to get current user info:', err))

    return () => {
      isMounted = false
    }
  }, [alert])

  if (!alert) return null

  const handleAssignChange = async (e) => {
    const val = e.target.value
    setError('')
    try {
      let updated
      if (val === '') {
        return
      } else if (currentUser && parseInt(val) === currentUser.id) {
        updated = await assignAlertToMe(alert.id)
      } else {
        updated = await assignAlert(alert.id, parseInt(val))
      }
      if (onUpdate && updated) {
        onUpdate(updated)
      }
    } catch (err) {
      setError(err.message || 'Failed to assign alert')
    }
  }

  const handleStatusChange = async (e) => {
    const val = e.target.value
    setError('')
    try {
      const updated = await updateAlertStatus(alert.id, val)
      if (onUpdate && updated) {
        onUpdate(updated)
      }
    } catch (err) {
      setError(err.message || 'Failed to update alert status')
    }
  }

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-96 bg-soc-card border-l border-soc-border shadow-2xl overflow-y-auto z-50 transform transition-transform duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-soc-border sticky top-0 bg-soc-card">
          <h2 className="text-xl font-bold text-soc-text">Alert Details</h2>
           <button
             onClick={onClose}
             className="p-2 hover:bg-soc-bg rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
           >
             <X size={20} />
           </button>
        </div>

        {/* Content */}
        <div className="p-6 pb-20 space-y-6">
          {/* Severity Badge */}
          <div>
            <p className="text-soc-secondary text-sm font-medium mb-2">Severity</p>
            <span
              className="inline-block px-4 py-2 rounded-lg font-bold text-white"
              style={{ backgroundColor: getSeverityColor(alert.severity) }}
            >
              {alert.severity}
            </span>
          </div>
         {/* Details Grid */}
         <div className="space-y-4 mt-6">
            {[
              { label: 'Alert ID', value: `#ALT-${alert.id}` },
              { label: 'Timestamp', value: alert.timestamp },
              { label: 'Source', value: alert.source },
              { label: 'Source IP', value: alert.ip },
              { label: 'Destination IP', value: alert.destIp },
              { label: 'Rule Name', value: alert.rule },
              { label: 'Rule Category', value: alert.category },
              { label: 'Protocol', value: alert.protocol },
              { label: 'Port', value: alert.port },
            ].map((item, idx) => (
              <div key={idx} className="pb-4 border-b border-soc-border">
                <p className="text-soc-secondary text-xs font-medium uppercase mb-1">{item.label}</p>
                <p className="text-soc-text font-mono text-sm break-all">{item.value}</p>
              </div>
            ))}
          </div>

          {/* Full Payload */}
          <div>
            <p className="text-soc-secondary text-sm font-medium mb-3">Alert Payload</p>
            <div className="bg-soc-bg p-4 rounded-lg border border-soc-border overflow-x-auto">
              <pre className="text-soc-muted text-xs font-mono whitespace-pre-wrap break-words leading-relaxed">
                {JSON.stringify(alert, null, 2)}
              </pre>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3 pt-4 border-t border-soc-border">
            {error && <p className="text-xs text-soc-critical">{error}</p>}
            
            <div>
              <label className="block text-xs font-semibold text-soc-secondary uppercase mb-1">Assignee</label>
              <select 
                value={alert.rawAssignedTo || ''} 
                onChange={handleAssignChange} 
                className="input-soc w-full"
                disabled={alert.rawStatus === 'RESOLVED'}
              >
                <option value="">Unassigned</option>
                {currentUser && (
                  <option value={currentUser.id}>Assign to Me ({currentUser.email})</option>
                )}
                {users.filter(u => !currentUser || u.id !== currentUser.id).map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.email} ({u.role})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-soc-secondary uppercase mb-1">Status</label>
              <select 
                value={alert.rawStatus} 
                onChange={handleStatusChange} 
                className="input-soc w-full"
                disabled={alert.rawStatus === 'RESOLVED'}
              >
                {alert.rawStatus === 'NEW' && <option value="NEW">Open</option>}
                <option value="IN_PROGRESS">Investigating</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
