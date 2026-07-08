import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function AlertsLineChart({ data: chartData }) {
  const resolvedData = Array.isArray(chartData) ? chartData : []

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={resolvedData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#e2e8f0',
          }}
        />
        <Line
          type="monotone"
          dataKey="alerts"
          stroke="#3b82f6"
          dot={{ fill: '#3b82f6', r: 4 }}
          activeDot={{ r: 6 }}
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
