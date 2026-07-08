import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, Shield, TrendingUp } from 'lucide-react'
import StatCard from '../components/StatCard'
import ChartCard from '../components/ChartCard'
import AlertsLineChart from '../components/Charts/AlertsLineChart'
import SeverityPieChart from '../components/Charts/SeverityPieChart'
import {
  buildAlertsLineData,
  buildSeverityData,
  formatTimeAgo,
  getAlerts,
  mapSeverityLabel,
  mapStatusLabel,
  getWebSocketUrl,
} from '../services/api'

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

export default function Dashboard() {
  const [alerts, setAlerts] = useState([])
  const [totalAlerts, setTotalAlerts] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    const loadData = async () => {
      setIsLoading(true)
      setError('')

      try {
        const alertsResponse = await getAlerts({ page: 1, limit: 200 })

        if (isMounted) {
          setAlerts(alertsResponse.alerts || [])
          setTotalAlerts(alertsResponse.total || 0)
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load dashboard data')
          setAlerts([])
          setTotalAlerts(0)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    let ws
    let reconnectTimeout
    let isCancelled = false

    const connectWs = () => {
      try {
        const wsUrl = getWebSocketUrl()
        ws = new WebSocket(wsUrl)

        ws.onmessage = (event) => {
          try {
            const newAlert = JSON.parse(event.data)
            setAlerts((prev) => {
              if (prev.some((a) => a.id === newAlert.id)) {
                return prev
              }
              return [newAlert, ...prev]
            })
            setTotalAlerts((prev) => prev + 1)
          } catch (err) {
            console.error('Failed to parse incoming dashboard alert:', err)
          }
        }

        ws.onclose = () => {
          if (!isCancelled) {
            console.log('Dashboard WebSocket disconnected. Reconnecting in 3s...')
            reconnectTimeout = setTimeout(connectWs, 3000)
          }
        }

        ws.onerror = (err) => {
          console.error('Dashboard WebSocket error:', err)
          ws.close()
        }
      } catch (err) {
        console.error('Dashboard WebSocket connection setup failed:', err)
        if (!isCancelled) {
          reconnectTimeout = setTimeout(connectWs, 3000)
        }
      }
    }

    connectWs()

    return () => {
      isCancelled = true
      if (ws) ws.close()
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    }
  }, [])

  const criticalAlerts = useMemo(
    () => alerts.filter((alert) => ['Critical', 'High'].includes(mapSeverityLabel(alert.severity))).length,
    [alerts],
  )

  const openAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const status = mapStatusLabel(alert.status)
      return status !== 'Resolved'
    }).length
  }, [alerts])

  const alertsToday = useMemo(() => {
    const today = new Date().toDateString()
    return alerts.filter((alert) => new Date(alert.created_at).toDateString() === today).length
  }, [alerts])

  const recentAlerts = useMemo(
    () =>
      alerts.slice(0, 5).map((alert) => ({
        id: alert.id,
        severity: mapSeverityLabel(alert.severity),
        source: `Device ${alert.device_id}`,
        ip: '-',
        rule: alert.type || alert.description || 'Security Alert',
        time: formatTimeAgo(alert.created_at),
        status: mapStatusLabel(alert.status),
      })),
    [alerts],
  )

  const lineChartData = useMemo(() => buildAlertsLineData(alerts), [alerts])
  const severityData = useMemo(() => buildSeverityData(alerts), [alerts])

  return (
    <div className="space-y-8 p-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-soc-text mb-2">Dashboard</h1>
        <p className="text-section-subtitle">Real-time security monitoring and threat analysis</p>
      </div>

      {error && <p className="text-sm text-soc-critical">{error}</p>}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={AlertCircle}
          label="Total Alerts"
          value={isLoading ? '...' : String(totalAlerts)}
          subtitle="All time"
        />
        <StatCard
          icon={Shield}
          label="Critical Alerts"
          value={isLoading ? '...' : String(criticalAlerts)}
          subtitle="Requires attention"
        />
        <StatCard
          icon={AlertCircle}
          label="Open Alerts"
          value={isLoading ? '...' : String(openAlerts)}
          subtitle="Not resolved"
        />
        <StatCard
          icon={TrendingUp}
          label="Alerts Today"
          value={isLoading ? '...' : String(alertsToday)}
          subtitle="Last 24 hours"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Alerts Over Time">
          <AlertsLineChart data={lineChartData} />
        </ChartCard>
        <ChartCard title="Severity Distribution">
          <SeverityPieChart data={severityData} />
        </ChartCard>
      </div>

      {/* Recent Alerts */}
      <ChartCard title="Recent Alerts">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-soc-border">
                 <th className="table-cell-muted text-label">Time</th>
                 <th className="table-cell-muted text-label">Severity</th>
                 <th className="table-cell-muted text-label">Source</th>
                 <th className="table-cell-muted text-label">IP</th>
                 <th className="table-cell-muted text-label">Rule</th>
                 <th className="table-cell-muted text-label">Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={6}>Loading recent alerts...</td>
                </tr>
              )}

              {!isLoading && recentAlerts.length === 0 && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={6}>No alerts found.</td>
                </tr>
              )}

              {recentAlerts.map((alert) => (
                <tr key={alert.id} className="border-b border-soc-border hover:bg-soc-bg transition-colors duration-200">
                  <td className="table-cell">{alert.time}</td>
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
                  <td className="table-cell">{alert.rule}</td>
                  <td className="table-cell">
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-soc-info bg-opacity-10 text-soc-info">
                      {alert.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  )
}
