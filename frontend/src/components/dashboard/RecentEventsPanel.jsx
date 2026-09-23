import SeverityBadge from '../security/SeverityBadge'
import EmptyState from '../common/EmptyState'
import { formatRelativeTime } from '../../utils/formatting'

export default function RecentEventsPanel({ events }) {
  if (!events || events.length === 0) {
    return <EmptyState title="No security events yet" message="Events appear here when an access request is denied." />
  }

  return (
    <ul className="divide-y divide-border-subtle">
      {events.map((event) => (
        <li key={event.id} className="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
          <div className="min-w-0">
            <p className="truncate text-sm text-text-primary">{event.event_type}</p>
            <p className="truncate text-xs text-text-muted">
              {event.user || 'unknown user'} → {event.resource || 'unknown resource'}
            </p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <SeverityBadge severity={event.severity} />
            <span className="text-[11px] text-text-muted">{formatRelativeTime(event.timestamp)}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}
