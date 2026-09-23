import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import EmptyState from '../common/EmptyState'

/** Generic horizontal-label bar chart for a { key: count } distribution map. */
export default function DistributionBarChart({ distribution, color = '#6366f1', emptyTitle, emptyMessage }) {
  const data = Object.entries(distribution || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  if (data.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262b38" horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={{ stroke: '#262b38' }} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={100}
          tick={{ fill: '#9ca3af', fontSize: 12 }}
          axisLine={{ stroke: '#262b38' }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{ background: '#191d27', border: '1px solid #262b38', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#e5e7eb' }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} fill={color} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  )
}
