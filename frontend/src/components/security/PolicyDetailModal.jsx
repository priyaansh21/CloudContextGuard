import Modal from '../common/Modal'
import Badge from '../common/Badge'
import { formatDateTime } from '../../utils/formatting'

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className="text-sm text-text-primary">{value ?? '—'}</p>
    </div>
  )
}

export default function PolicyDetailModal({ policy, onClose }) {
  if (!policy) return null

  return (
    <Modal open={Boolean(policy)} onClose={onClose} title={`Policy — ${policy.name}`}>
      <div className="mb-4 flex items-center justify-between">
        <Badge
          tone={
            policy.is_enabled
              ? { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
              : { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
          }
        >
          {policy.is_enabled ? 'ENABLED' : 'DISABLED'}
        </Badge>
        <span className="text-xs text-text-muted">Updated {formatDateTime(policy.updated_at)}</span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Resource" value={policy.resource} />
        <Field label="Required Role" value={policy.required_role || 'None'} />
        <Field label="Trusted VPC" value={policy.trusted_vpc || 'None'} />
        <Field label="MFA Required" value={policy.mfa_required ? 'Yes' : 'No'} />
        <Field label="Max Risk Score" value={policy.max_risk_score ?? 'No limit'} />
        <Field label="External Access Allowed" value={policy.external_access_allowed ? 'Yes' : 'No'} />
        <Field label="Created" value={formatDateTime(policy.created_at)} />
      </div>
      <div className="mt-4">
        <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Description</p>
        <p className="rounded-md border border-border bg-surface-2 p-3 text-sm text-text-secondary">
          {policy.description || 'No description provided.'}
        </p>
      </div>
    </Modal>
  )
}
