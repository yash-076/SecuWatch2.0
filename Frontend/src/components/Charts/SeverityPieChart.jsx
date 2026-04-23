import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts'

const data = [
  { name: 'Critical', value: 24 },
  { name: 'High', value: 58 },
  { name: 'Medium', value: 96 },
  { name: 'Low', value: 142 },
  { name: 'Info', value: 78 },
]

const COLORS = {
  Critical: '#ef4444',
  High: '#f97316',
  Medium: '#f59e0b',
  Low: '#22c55e',
  Info: '#3b82f6',
}

export default function SeverityPieChart({ data: chartData }) {
  const resolvedData = chartData && chartData.length ? chartData : data

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
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#e2e8f0',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
