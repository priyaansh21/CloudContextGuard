import { cn } from '../../utils/formatting'

export default function Card({ title, subtitle, action, children, className, bodyClassName }) {
  return (
    <div className={cn('rounded-lg border border-border bg-surface-1', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
          <div>
            {title && <h3 className="text-sm font-semibold text-text-primary">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={cn('p-4', bodyClassName)}>{children}</div>
    </div>
  )
}
