import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import EmptyState from '../common/EmptyState'

const ORDER = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const COLORS = { LOW: '#22c55e', MEDIUM: '#38bdf8', HIGH: '#f59e0b', CRITICAL: '#ef4444' }

export default function RiskChart({ distribution }) {
  const data = ORDER.map((level) => ({ name: level, value: distribution?.[level] || 0 }))
  const hasData = data.some((d) => d.value > 0)

  if (!hasData) {
    return <EmptyState title="No risk data yet" message="Risk levels appear once access requests are evaluated." />
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262b38" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={{ stroke: '#262b38' }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={{ stroke: '#262b38' }} tickLine={false} />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{ background: '#191d27', border: '1px solid #262b38', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#e5e7eb' }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
