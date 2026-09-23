import { useMemo, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { getSecurityEvents } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import SelectFilter from '../components/common/SelectFilter'
import { TableShell, SortableHeader } from '../components/tables/TableShell'
import { TableSkeleton } from '../components/common/LoadingState'
import SeverityBadge from '../components/security/SeverityBadge'
import SecurityEventDetailModal from '../components/security/SecurityEventDetailModal'
import { formatDateTime } from '../utils/formatting'

const SEVERITY_OPTIONS = [
  { value: 'ALL', label: 'All severities' },
  { value: 'LOW', label: 'LOW' },
  { value: 'MEDIUM', label: 'MEDIUM' },
  { value: 'HIGH', label: 'HIGH' },
  { value: 'CRITICAL', label: 'CRITICAL' },
]

export default function SecurityEvents() {
  const { data, loading, error, reload } = useApi(getSecurityEvents)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [userFilter, setUserFilter] = useState('ALL')
  const [resourceFilter, setResourceFilter] = useState('ALL')
  const [selected, setSelected] = useState(null)

  const userOptions = useMemo(() => {
    const unique = Array.from(new Set((data || []).map((e) => e.user).filter(Boolean)))
    return [{ value: 'ALL', label: 'All users' }, ...unique.map((u) => ({ value: u, label: u }))]
  }, [data])

  const resourceOptions = useMemo(() => {
    const unique = Array.from(new Set((data || []).map((e) => e.resource).filter(Boolean)))
    return [{ value: 'ALL', label: 'All resources' }, ...unique.map((r) => ({ value: r, label: r }))]
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    return data.filter((event) => {
      if (severityFilter !== 'ALL' && event.severity !== severityFilter) return false
      if (userFilter !== 'ALL' && event.user !== userFilter) return false
      if (resourceFilter !== 'ALL' && event.resource !== resourceFilter) return false
      return true
    })
  }, [data, severityFilter, userFilter, resourceFilter])

  if (error) return <ErrorState message={error.message} onRetry={reload} />

  return (
    <div className="space-y-4">
      <Card title="Security Events" subtitle={data ? `${filtered.length} of ${data.length} events` : undefined}>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <SelectFilter label="Severity" value={severityFilter} onChange={setSeverityFilter} options={SEVERITY_OPTIONS} />
          <SelectFilter label="User" value={userFilter} onChange={setUserFilter} options={userOptions} />
          <SelectFilter label="Resource" value={resourceFilter} onChange={setResourceFilter} options={resourceOptions} />
        </div>

        {loading ? (
          <TableSkeleton rows={6} cols={8} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No security events found"
            message={data && data.length > 0 ? 'Try adjusting your filters.' : 'Events appear here when an access request is denied.'}
          />
        ) : (
          <TableShell>
            <thead>
              <tr>
                <SortableHeader label="Severity" />
                <SortableHeader label="Timestamp" />
                <SortableHeader label="Event Type" />
                <SortableHeader label="User" />
                <SortableHeader label="Source IP" />
                <SortableHeader label="Source VPC" />
                <SortableHeader label="Resource" />
                <SortableHeader label="Risk" />
                <SortableHeader label="Action Taken" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((event) => (
                <tr
                  key={event.id}
                  onClick={() => setSelected(event)}
                  tabIndex={0}
                  role="button"
                  aria-label={`View details for security event ${event.id}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') setSelected(event)
                  }}
                  className="cursor-pointer border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60 hover:bg-surface-3"
                >
                  <td className="whitespace-nowrap px-3 py-2.5">
                    <SeverityBadge severity={event.severity} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{formatDateTime(event.timestamp)}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-primary">{event.event_type}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.user || '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.source_ip || '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.source_vpc || '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.resource || '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.risk_score ?? '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{event.action_taken || '—'}</td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </Card>

      <SecurityEventDetailModal event={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
