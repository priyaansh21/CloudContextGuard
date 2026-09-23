import { useApi } from '../hooks/useApi'
import { getAlerts } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import SeverityBadge from '../components/security/SeverityBadge'
import { Skeleton } from '../components/common/LoadingState'
import { cn, formatDateTime, statusTone } from '../utils/formatting'

export default function Alerts() {
  const { data, loading, error, reload } = useApi(getAlerts)

  if (error) return <ErrorState message={error.message} onRetry={reload} />

  return (
    <Card title="Alerts" subtitle={data ? `${data.length} alert(s)` : undefined}>
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState title="No alerts" message="Alerts are raised automatically when a request is assessed as HIGH or CRITICAL risk." />
      ) : (
        <div className="space-y-3">
          {data.map((alert) => (
            <div
              key={alert.id}
              className={cn(
                'rounded-lg border p-4',
                alert.severity === 'CRITICAL' ? 'border-status-critical/40 bg-status-critical-bg' : 'border-border bg-surface-2'
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-semibold text-text-primary">{alert.title}</p>
                  <p className="mt-1 text-sm text-text-secondary">{alert.description}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <SeverityBadge severity={alert.severity} />
                  <Badge tone={statusTone(alert.status)}>{alert.status}</Badge>
                </div>
              </div>
              <p className="mt-2 text-xs text-text-muted">{formatDateTime(alert.timestamp)}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
