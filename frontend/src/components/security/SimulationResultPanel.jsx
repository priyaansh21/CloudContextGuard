import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import DecisionBadge from './DecisionBadge'
import RiskBadge from './RiskBadge'
import PassFailBadge from './PassFailBadge'
import AccessDecisionCard from './AccessDecisionCard'
import AccessBlockedBanner from './AccessBlockedBanner'
import RiskFactorsList from './RiskFactorsList'
import AttackTimeline from './AttackTimeline'

const PIPELINE_STAGES = ['IDENTITY', 'NETWORK CONTEXT', 'RESOURCE POLICY', 'MFA', 'RISK ENGINE']

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className="text-sm text-text-primary">{value ?? '—'}</p>
    </div>
  )
}

function RunningState() {
  return (
    <div className="flex flex-col items-center gap-4 py-10 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-status-info" aria-hidden="true" />
      <p className="text-sm font-semibold tracking-wide text-text-primary">ANALYZING REQUEST...</p>
      <div className="flex flex-wrap justify-center gap-2">
        {PIPELINE_STAGES.map((stage) => (
          <span key={stage} className="rounded-full border border-border bg-surface-2 px-3 py-1 text-[11px] font-medium text-text-secondary">
            {stage}
          </span>
        ))}
      </div>
    </div>
  )
}

function FailedState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center">
      <AlertTriangle className="h-8 w-8 text-status-critical" aria-hidden="true" />
      <p className="text-sm font-bold tracking-wide text-status-critical">SIMULATION FAILED</p>
      <p className="max-w-sm text-sm text-text-secondary">API unavailable or request could not be evaluated.</p>
      {message && <p className="max-w-sm text-xs text-text-muted">{message}</p>}
      <button
        type="button"
        onClick={onRetry}
        className="mt-1 inline-flex items-center gap-2 rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-3"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" />
        Retry
      </button>
    </div>
  )
}

function AccessEvaluationFields({ payload, role }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Field label="User" value={payload.user} />
      <Field label="Role" value={role} />
      <Field label="Action" value={payload.action} />
      <Field label="Resource" value={payload.resource} />
      <Field label="Source IP" value={payload.source_ip} />
      <Field label="Source VPC" value={payload.source_vpc} />
      <Field label="MFA" value={payload.mfa ? 'Provided' : 'Not provided'} />
    </div>
  )
}

function SingleResult({ scenario, role, response, securityEvent, alert }) {
  const showBlockedBanner = response.decision === 'DENY'

  return (
    <div className="space-y-5">
      <AccessEvaluationFields payload={scenario.requestPayload} role={role} />

      {showBlockedBanner && (
        <AccessBlockedBanner
          iamResult={response.iam_result.result}
          vpcResult={response.vpc_result.result}
          mfaResult={response.mfa_result.result}
          riskLevel={response.risk_level}
          riskScore={response.risk_score}
        />
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Why was it allowed/denied?</p>
            <p className="rounded-md border border-border bg-surface-2 p-3 text-sm text-text-secondary">{response.reason}</p>
          </div>
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Risk Factors</p>
            <RiskFactorsList factors={response.risk_factors} />
            <p className="mt-2 text-xs text-text-muted">
              Final Risk: <span className="font-mono font-semibold text-text-primary">{response.risk_score}</span> / {response.risk_level}
            </p>
          </div>
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Attack Timeline</p>
            <AttackTimeline securityEventCreated={Boolean(securityEvent)} alertCreated={Boolean(alert)} />
          </div>
        </div>

        <AccessDecisionCard
          request={{
            action: scenario.requestPayload.action,
            resource: scenario.requestPayload.resource,
            iamResult: response.iam_result.result,
            vpcResult: response.vpc_result.result,
            resourceResult: response.resource_result.result,
            mfaResult: response.mfa_result.result,
            riskScore: response.risk_score,
            riskLevel: response.risk_level,
            decision: response.decision,
          }}
        />
      </div>
    </div>
  )
}

function RepeatedResult({ scenario, role, attempts, securityEvent, alert }) {
  const last = attempts[attempts.length - 1]

  return (
    <div className="space-y-5">
      <AccessEvaluationFields payload={scenario.requestPayload} role={role} />

      <div>
        <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Sequential Attempts</p>
        <div className="space-y-2">
          {attempts.map((attempt) => (
            <div
              key={attempt.attemptNumber}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-surface-2 px-3 py-2"
            >
              <span className="text-sm font-semibold text-text-primary">Attempt {attempt.attemptNumber}</span>
              <div className="flex flex-wrap items-center gap-2">
                <PassFailBadge result={attempt.response.iam_result.result} />
                <RiskBadge level={attempt.response.risk_level} score={attempt.response.risk_score} />
                <DecisionBadge decision={attempt.response.decision} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Final Attempt - Why was it allowed/denied?</p>
            <p className="rounded-md border border-border bg-surface-2 p-3 text-sm text-text-secondary">{last.response.reason}</p>
          </div>
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Final Attempt - Risk Factors</p>
            <RiskFactorsList factors={last.response.risk_factors} />
            <p className="mt-2 text-xs text-text-muted">
              Final Risk: <span className="font-mono font-semibold text-text-primary">{last.response.risk_score}</span> / {last.response.risk_level}
            </p>
          </div>
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Attack Timeline (final attempt)</p>
            <AttackTimeline securityEventCreated={Boolean(securityEvent)} alertCreated={Boolean(alert)} />
          </div>
        </div>

        <AccessDecisionCard
          request={{
            action: scenario.requestPayload.action,
            resource: scenario.requestPayload.resource,
            iamResult: last.response.iam_result.result,
            vpcResult: last.response.vpc_result.result,
            resourceResult: last.response.resource_result.result,
            mfaResult: last.response.mfa_result.result,
            riskScore: last.response.risk_score,
            riskLevel: last.response.risk_level,
            decision: last.response.decision,
          }}
        />
      </div>
    </div>
  )
}

export default function SimulationResultPanel({ scenario, role, result, onRetry }) {
  if (!scenario || !result) return null

  return (
    <Card
      title={`Simulation Result — ${scenario.name}`}
      action={<Badge tone={{ text: 'text-status-info', bg: 'bg-status-info-bg', border: 'border-status-info/30' }}>{scenario.threatLevel}</Badge>}
    >
      {result.status === 'running' && <RunningState />}
      {result.status === 'error' && <FailedState message={result.message} onRetry={onRetry} />}
      {result.status === 'success' &&
        (scenario.repeated ? (
          <RepeatedResult scenario={scenario} role={role} attempts={result.attempts} securityEvent={result.securityEvent} alert={result.alert} />
        ) : (
          <SingleResult scenario={scenario} role={role} response={result.response} securityEvent={result.securityEvent} alert={result.alert} />
        ))}
    </Card>
  )
}
