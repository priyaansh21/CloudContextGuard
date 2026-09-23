import { ArrowDown } from 'lucide-react'
import PassFailBadge from './PassFailBadge'
import DecisionBadge from './DecisionBadge'
import RiskBadge from './RiskBadge'
import { cn } from '../../utils/formatting'

function FlowStep({ label, children }) {
  return (
    <>
      <div className="flex items-center justify-between rounded-md border border-border bg-surface-2 px-3 py-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">{label}</span>
        {children}
      </div>
      <ArrowDown className="mx-auto h-4 w-4 text-text-muted" aria-hidden="true" />
    </>
  )
}

/**
 * Visualizes the request -> IAM -> VPC -> MFA -> Risk -> Decision pipeline
 * for a single access request, using whatever result data is available.
 */
export default function AccessDecisionCard({ request }) {
  const {
    action,
    resource,
    iamResult,
    vpcResult,
    resourceResult,
    mfaResult,
    riskScore,
    riskLevel,
    decision,
  } = request

  return (
    <div className="space-y-1.5">
      <div
        className={cn(
          'rounded-md border px-3 py-2 text-center text-sm font-medium',
          'border-status-accent/30 bg-status-accent/10 text-text-primary'
        )}
      >
        REQUEST — {action} on {resource || 'unknown resource'}
      </div>
      <ArrowDown className="mx-auto h-4 w-4 text-text-muted" aria-hidden="true" />

      <FlowStep label="IAM">
        <PassFailBadge result={iamResult} />
      </FlowStep>
      <FlowStep label="VPC">
        <PassFailBadge result={vpcResult} />
      </FlowStep>
      <FlowStep label="Resource Policy">
        <PassFailBadge result={resourceResult} />
      </FlowStep>
      <FlowStep label="MFA">
        <PassFailBadge result={mfaResult} />
      </FlowStep>
      <FlowStep label="Risk">
        <RiskBadge level={riskLevel} score={riskScore} />
      </FlowStep>

      <div
        className={cn(
          'rounded-md border px-3 py-2.5 text-center text-sm font-bold tracking-wide',
          decision === 'ALLOW'
            ? 'border-status-safe/40 bg-status-safe-bg text-status-safe'
            : 'border-status-critical/40 bg-status-critical-bg text-status-critical'
        )}
      >
        FINAL DECISION: {decision}
      </div>
    </div>
  )
}
