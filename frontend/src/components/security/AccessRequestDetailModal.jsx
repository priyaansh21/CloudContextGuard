import Modal from '../common/Modal'
import AccessDecisionCard from './AccessDecisionCard'
import RiskFactorsList from './RiskFactorsList'
import { formatDateTime } from '../../utils/formatting'

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className="text-sm text-text-primary">{value ?? '—'}</p>
    </div>
  )
}

export default function AccessRequestDetailModal({ request, onClose }) {
  if (!request) return null

  return (
    <Modal open={Boolean(request)} onClose={onClose} title={`Access Request #${request.id}`} wide>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="User" value={request.user} />
            <Field label="Role" value={request.role} />
            <Field label="Action" value={request.action} />
            <Field label="Resource" value={request.resource} />
            <Field label="Source IP" value={request.source_ip} />
            <Field label="Source VPC" value={request.source_vpc} />
            <Field label="MFA Provided" value={request.mfa ? 'Yes' : 'No'} />
            <Field label="Request Type" value={request.request_type} />
            <Field label="Timestamp" value={formatDateTime(request.timestamp)} />
          </div>

          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Decision Reason</p>
            <p className="rounded-md border border-border bg-surface-2 p-3 text-sm text-text-secondary">
              {request.decision_reason || 'No reason recorded.'}
            </p>
          </div>

          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Risk Factors</p>
            <RiskFactorsList factors={request.risk_factors} />
          </div>
        </div>

        <AccessDecisionCard
          request={{
            action: request.action,
            resource: request.resource,
            iamResult: request.iam_result,
            vpcResult: request.vpc_result,
            resourceResult: request.resource_result,
            mfaResult: request.mfa_result,
            riskScore: request.risk_score,
            riskLevel: request.risk_level,
            decision: request.final_decision,
          }}
        />
      </div>
    </Modal>
  )
}
