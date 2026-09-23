import { ShieldAlert } from 'lucide-react'
import PassFailBadge from './PassFailBadge'
import RiskBadge from './RiskBadge'

/**
 * Prominent banner shown for any denied request. Values shown are the
 * actual backend results passed in as props - this component adds
 * explanatory framing only, never a substitute decision. The subtitle
 * wording reflects whether IAM itself actually passed, so it never claims
 * "valid identity" when the identity's permission check failed.
 */
export default function AccessBlockedBanner({ iamResult, vpcResult, mfaResult, riskLevel, riskScore }) {
  const iamPassed = iamResult === 'PASS' || iamResult === true

  return (
    <div className="rounded-lg border-2 border-status-critical/40 bg-status-critical-bg p-5">
      <div className="flex items-center gap-2">
        <ShieldAlert className="h-6 w-6 text-status-critical" aria-hidden="true" />
        <p className="text-lg font-extrabold tracking-wide text-status-critical">ACCESS BLOCKED</p>
      </div>
      <p className="mt-2 text-sm text-text-secondary">
        {iamPassed
          ? 'Valid identity detected, but contextual authorization failed.'
          : 'Identity or permission check failed - access was denied at the earliest evaluation stage.'}
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-text-muted">IAM</p>
          <PassFailBadge result={iamResult} />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wide text-text-muted">VPC</p>
          <PassFailBadge result={vpcResult} />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wide text-text-muted">MFA</p>
          <PassFailBadge result={mfaResult} />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wide text-text-muted">Risk</p>
          <RiskBadge level={riskLevel} score={riskScore} />
        </div>
      </div>
      <p className="mt-4 text-sm font-bold text-status-critical">FINAL: DENIED</p>
    </div>
  )
}
