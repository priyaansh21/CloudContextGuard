import { Check, Minus } from 'lucide-react'
import { cn } from '../../utils/formatting'

/**
 * Renders the evaluation pipeline as a timeline. The first six steps always
 * ran (a response was returned), so they're always marked complete. The
 * last two steps - Security Event and Alert - are only marked complete
 * when the caller has confirmed their existence via a real API lookup
 * (e.g. matching access_request_id), never assumed.
 */
export default function AttackTimeline({ securityEventCreated, alertCreated }) {
  const steps = [
    { label: 'REQUEST RECEIVED', done: true },
    { label: 'IAM EVALUATION', done: true },
    { label: 'VPC EVALUATION', done: true },
    { label: 'MFA EVALUATION', done: true },
    { label: 'RISK CALCULATION', done: true },
    { label: 'POLICY DECISION', done: true },
    { label: 'SECURITY EVENT', done: securityEventCreated, skippedLabel: 'Not created (access allowed)' },
    { label: 'ALERT', done: alertCreated, skippedLabel: 'Not created (risk below alert threshold)' },
  ]

  return (
    <ol className="space-y-0">
      {steps.map((step, index) => (
        <li key={step.label} className="flex gap-3">
          <div className="flex flex-col items-center">
            <span
              className={cn(
                'flex h-6 w-6 shrink-0 items-center justify-center rounded-full border',
                step.done
                  ? 'border-status-safe/40 bg-status-safe-bg text-status-safe'
                  : 'border-border bg-surface-2 text-text-muted'
              )}
            >
              {step.done ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Minus className="h-3.5 w-3.5" aria-hidden="true" />}
            </span>
            {index < steps.length - 1 && <span className="h-6 w-px bg-border" />}
          </div>
          <div className="pb-3">
            <p className={cn('text-sm font-semibold', step.done ? 'text-text-primary' : 'text-text-muted')}>{step.label}</p>
            {!step.done && step.skippedLabel && <p className="text-xs text-text-muted">{step.skippedLabel}</p>}
          </div>
        </li>
      ))}
    </ol>
  )
}
