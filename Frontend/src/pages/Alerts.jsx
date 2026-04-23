import { useEffect, useState } from 'react'
import FiltersBar from '../components/FiltersBar'
import AlertDrawer from '../components/AlertDrawer'
import { formatDateTime, getAlerts, mapSeverityLabel, mapStatusLabel } from '../services/api'

const mapAlertToUi = (alert) => ({
  id: alert.id,
  severity: mapSeverityLabel(alert.severity),
  source: `Device ${alert.device_id}`,
  ip: '-',
  destIp: '-',
  rule: alert.type || alert.description || 'Security Alert',
  category: alert.type || 'Security',
  protocol: '-',
  port: '-',
  timestamp: formatDateTime(alert.created_at),
  status: mapStatusLabel(alert.status),
  assignee: alert.assigned_to ? `User #${alert.assigned_to}` : 'Unassigned',
  description: alert.description,
})

const getSeverityColor = (severity) => {
  const colors = {
    Critical: '#ef4444',
    High: '#f97316',
    Medium: '#f59e0b',
    Low: '#22c55e',
    Info: '#3b82f6',
  }
  return colors[severity] || '#e2e8f0'
}

const getSeverityBgColor = (severity) => {
  const colors = {
    Critical: 'bg-red-500 bg-opacity-10',
    High: 'bg-orange-500 bg-opacity-10',
    Medium: 'bg-yellow-500 bg-opacity-10',
    Low: 'bg-green-500 bg-opacity-10',
    Info: 'bg-blue-500 bg-opacity-10',
  }
  return colors[severity] || 'bg-gray-500 bg-opacity-10'
}

const getStatusBgColor = (status) => {
  const colors = {
    Open: 'bg-red-500 bg-opacity-10 text-soc-critical',
    Acknowledged: 'bg-yellow-500 bg-opacity-10 text-soc-medium',
    Investigating: 'bg-blue-500 bg-opacity-10 text-soc-info',
    Resolved: 'bg-green-500 bg-opacity-10 text-soc-low',
  }
  return colors[status] || 'bg-gray-500 bg-opacity-10'
}

export default function Alerts() {
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [alertsData, setAlertsData] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    const loadAlerts = async () => {
      setIsLoading(true)
      setError('')

      try {
        const response = await getAlerts({ page: 1, limit: 100 })

        if (isMounted) {
          setAlertsData((response.alerts || []).map(mapAlertToUi))
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load alerts')
          setAlertsData([])
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadAlerts()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="space-y-6 p-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-soc-text mb-2">Alerts</h1>
        <p className="text-section-subtitle">Manage and analyze security alerts in real-time</p>
      </div>

      {error && <p className="text-sm text-soc-critical">{error}</p>}

      {/* Filters */}
      <FiltersBar />

      {/* Alerts Table */}
      <div className="card-base p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-soc-border bg-soc-bg">
                <th className="table-cell-muted text-label">Time</th>
                <th className="table-cell-muted text-label">Severity</th>
                <th className="table-cell-muted text-label">Source</th>
                <th className="table-cell-muted text-label">IP</th>
                <th className="table-cell-muted text-label">Rule</th>
                <th className="table-cell-muted text-label">Status</th>
                <th className="table-cell-muted text-label">Assignee</th>
                <th className="table-cell-muted text-label">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={8}>Loading alerts...</td>
                </tr>
              )}

              {!isLoading && alertsData.length === 0 && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={8}>No alerts found.</td>
                </tr>
              )}

              {alertsData.map((alert) => (
                <tr
                  key={alert.id}
                  onClick={() => setSelectedAlert(alert)}
                  className="table-row hover:shadow-soc-sm transition-smooth group cursor-pointer"
                  style={{
                    borderLeftColor: getSeverityColor(alert.severity),
                    borderLeftWidth: '4px',
                  }}
                >
                  <td className="table-cell text-xs">{alert.timestamp}</td>
                  <td className="table-cell">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityBgColor(alert.severity)}`}
                      style={{ color: getSeverityColor(alert.severity) }}
                    >
                      {alert.severity}
                    </span>
                  </td>
                  <td className="table-cell">{alert.source}</td>
                  <td className="table-cell font-mono text-xs">{alert.ip}</td>
                  <td className="table-cell max-w-xs truncate">{alert.rule}</td>
                  <td className="table-cell">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBgColor(alert.status)}`}>
                      {alert.status}
                    </span>
                  </td>
                  <td className="table-cell text-sm">
                    {alert.assignee === 'Unassigned' ? (
                      <span className="text-soc-muted italic">Unassigned</span>
                    ) : (
                      alert.assignee
                    )}
                  </td>
                  <td className="table-cell">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedAlert(alert)
                      }}
                      className="text-soc-info hover:text-blue-400 transition-smooth font-medium text-sm px-3 py-1 hover:bg-soc-info hover:bg-opacity-10 rounded"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alert Drawer */}
      <AlertDrawer alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
    </div>
  )
}
