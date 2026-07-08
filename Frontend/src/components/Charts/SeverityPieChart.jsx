import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = {
  Critical: '#ef4444',
  High: '#f97316',
  Medium: '#f59e0b',
  Low: '#22c55e',
  Info: '#e63946',
}

export default function SeverityPieChart({ data: chartData }) {
  const resolvedData = (Array.isArray(chartData) ? chartData : []).filter((item) => item.value > 0)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={resolvedData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, value }) => `${name}: ${value}`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {resolvedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: '#111111',
            border: '1px solid #1e1e1e',
            borderRadius: '8px',
            color: '#f0f0f0',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
          }}
        />
        <Legend wrapperStyle={{ color: '#8a8a8a', fontSize: '12px' }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
