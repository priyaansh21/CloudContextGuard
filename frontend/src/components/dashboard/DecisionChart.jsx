import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import EmptyState from '../common/EmptyState'

const COLORS = { ALLOW: '#22c55e', DENY: '#ef4444' }

export default function DecisionChart({ distribution }) {
  const data = Object.entries(distribution || {})
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }))

  if (data.length === 0) {
    return <EmptyState title="No access requests yet" message="Submit a request via the API to see decisions here." />
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name] || '#6366f1'} stroke="#12151c" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#191d27', border: '1px solid #262b38', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#e5e7eb' }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
