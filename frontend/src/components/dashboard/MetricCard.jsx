import { cn } from '../../utils/formatting'

export default function MetricCard({ label, value, icon: Icon, tone }) {
  const { text, bg } = tone || { text: 'text-text-primary', bg: 'bg-surface-2' }
  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</p>
        {Icon && (
          <span className={cn('flex h-7 w-7 items-center justify-center rounded-md', bg)}>
            <Icon className={cn('h-4 w-4', text)} aria-hidden="true" />
          </span>
        )}
      </div>
      <p className="mt-2 text-2xl font-bold text-text-primary">{value ?? '—'}</p>
    </div>
  )
}
