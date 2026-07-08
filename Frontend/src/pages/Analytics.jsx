import { useEffect, useMemo, useState } from 'react'
import ChartCard from '../components/ChartCard'
import AlertsLineChart from '../components/Charts/AlertsLineChart'
import SeverityPieChart from '../components/Charts/SeverityPieChart'
import TopIPsBarChart from '../components/Charts/TopIPsBarChart'
import {
  buildAlertsLineData,
  buildSeverityData,
  buildTopSourcesData,
  getAlerts,
} from '../services/api'

export default function Analytics() {
  const [alerts, setAlerts] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    const loadAnalytics = async () => {
      setIsLoading(true)
      setError('')

      try {
        const response = await getAlerts({ page: 1, limit: 200 })
        if (isMounted) {
          setAlerts(response.alerts || [])
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load analytics')
          setAlerts([])
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadAnalytics()

    return () => {
      isMounted = false
    }
  }, [])

  const lineData = useMemo(() => buildAlertsLineData(alerts), [alerts])
  const severityData = useMemo(() => buildSeverityData(alerts), [alerts])
  const topSourcesData = useMemo(() => buildTopSourcesData(alerts), [alerts])

  const resolvedAlerts = useMemo(
    () => alerts.filter((alert) => String(alert.status || '').toUpperCase() === 'RESOLVED'),
    [alerts],
  )

  const avgResponseHours = useMemo(() => {
    if (!resolvedAlerts.length) return null

    const totalMs = resolvedAlerts.reduce((sum, alert) => {
      const createdAt = new Date(alert.created_at).getTime()
      const updatedAt = new Date(alert.updated_at).getTime()
      if (Number.isNaN(createdAt) || Number.isNaN(updatedAt)) return sum
      return sum + Math.max(0, updatedAt - createdAt)
    }, 0)

    return totalMs / resolvedAlerts.length / (1000 * 60 * 60)
  }, [resolvedAlerts])

  const resolutionRate = useMemo(() => {
    if (!alerts.length) return '0.0%'
    return `${((resolvedAlerts.length / alerts.length) * 100).toFixed(1)}%`
  }, [alerts, resolvedAlerts])

  const falsePositiveRate = useMemo(() => {
    if (!resolvedAlerts.length) return '0.0%'
    const fps = resolvedAlerts.filter((alert) => {
      const desc = String(alert.description || '').toLowerCase()
      const type = String(alert.type || '').toLowerCase()
      return desc.includes('false positive') || desc.includes('fp') || type.includes('suspicious_ua')
    }).length
    return `${((fps / resolvedAlerts.length) * 100).toFixed(1)}%`
  }, [resolvedAlerts])

  const summaryStats = [
    {
      label: 'Avg. Response Time',
      value: avgResponseHours !== null ? `${avgResponseHours.toFixed(1)} hrs` : 'N/A',
      trend: '-',
    },
    { label: 'False Positive Rate', value: falsePositiveRate, trend: '-' },
    {
      label: 'MTTR (Mean Time To Resolve)',
      value: avgResponseHours !== null ? `${avgResponseHours.toFixed(1)} hrs` : 'N/A',
      trend: '-',
    },
    { label: 'Resolution Rate', value: resolutionRate, trend: '-' },
  ]

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-soc-text mb-2">Analytics</h1>
        <p className="text-section-subtitle">Comprehensive security insights and threat analysis</p>
      </div>

      {error && <p className="text-sm text-soc-critical">{error}</p>}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Alerts Over Time (48 Hours)">
          <AlertsLineChart data={lineData} />
        </ChartCard>
        <ChartCard title="Severity Distribution">
          <SeverityPieChart data={severityData} />
        </ChartCard>
      </div>

      {/* Top IPs */}
      <ChartCard title="Top Source IPs by Alert Count">
        <TopIPsBarChart data={topSourcesData} />
      </ChartCard>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryStats.map((stat, idx) => (
          <div key={idx} className="card-base p-4">
             <p className="text-label mb-3">{stat.label}</p>
             <p className="text-value text-2xl mb-3">{stat.value}</p>
            <p className="text-xs text-soc-muted">
              <span className={stat.trend.startsWith('-') ? 'text-soc-low' : 'text-soc-high'}>
                {stat.trend}
              </span>
              {isLoading ? ' loading...' : ' based on available alerts'}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
