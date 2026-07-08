import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function TopIPsBarChart({ data: chartData }) {
  const resolvedData = Array.isArray(chartData) ? chartData : []

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={resolvedData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e1e" />
        <XAxis dataKey="ip" stroke="#555555" tick={{ fill: '#8a8a8a', fontSize: 12 }} />
        <YAxis stroke="#555555" tick={{ fill: '#8a8a8a', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#111111',
            border: '1px solid #1e1e1e',
            borderRadius: '8px',
            color: '#f0f0f0',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
          }}
        />
        <Bar dataKey="count" fill="#e63946" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
