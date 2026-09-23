import Modal from '../common/Modal'
import SeverityBadge from './SeverityBadge'
import { formatDateTime } from '../../utils/formatting'

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className="text-sm text-text-primary">{value ?? '—'}</p>
    </div>
  )
}

export default function SecurityEventDetailModal({ event, onClose }) {
  if (!event) return null

  return (
    <Modal open={Boolean(event)} onClose={onClose} title={`Security Event #${event.id}`}>
      <div className="mb-4 flex items-center justify-between">
        <SeverityBadge severity={event.severity} />
        <span className="text-xs text-text-muted">{formatDateTime(event.timestamp)}</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Event Type" value={event.event_type} />
        <Field label="Action Taken" value={event.action_taken} />
        <Field label="User" value={event.user} />
        <Field label="Resource" value={event.resource} />
        <Field label="Source IP" value={event.source_ip} />
        <Field label="Source VPC" value={event.source_vpc} />
        <Field label="Risk Score" value={event.risk_score} />
      </div>
      <div className="mt-4">
        <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Description</p>
        <p className="rounded-md border border-border bg-surface-2 p-3 text-sm text-text-secondary">
          {event.description || 'No description recorded.'}
        </p>
      </div>
    </Modal>
  )
}
