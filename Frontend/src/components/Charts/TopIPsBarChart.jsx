import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const data = [
  { ip: '192.168.1.1', count: 45 },
  { ip: '192.168.1.5', count: 38 },
  { ip: '192.168.2.1', count: 32 },
  { ip: '192.168.2.5', count: 28 },
  { ip: '192.168.3.1', count: 22 },
  { ip: '192.168.3.5', count: 18 },
]

export default function TopIPsBarChart({ data: chartData }) {
  const resolvedData = chartData && chartData.length ? chartData : data

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={resolvedData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="ip" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            color: '#e2e8f0',
          }}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
