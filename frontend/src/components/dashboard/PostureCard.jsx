import { cn } from '../../utils/formatting'

export default function PostureCard({ title, status, description, icon: Icon }) {
  const healthy = status === 'ACTIVE' || status === 'PROTECTED'
  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-status-info" aria-hidden="true" />
          <p className="text-sm font-semibold text-text-primary">{title}</p>
        </div>
        <span
          className={cn(
            'rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wide',
            healthy ? 'border-status-safe/30 bg-status-safe-bg text-status-safe' : 'border-status-warning/30 bg-status-warning-bg text-status-warning'
          )}
        >
          {status}
        </span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-text-secondary">{description}</p>
    </div>
  )
}
