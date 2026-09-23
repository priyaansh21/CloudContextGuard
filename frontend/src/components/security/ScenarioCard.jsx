import { Crosshair, Loader2 } from 'lucide-react'
import Card from '../common/Card'
import Badge from '../common/Badge'
import { riskTone } from '../../utils/formatting'

export default function ScenarioCard({ scenario, onRun, isRunning, anyRunning }) {
  return (
    <Card title={scenario.name} action={<Badge tone={riskTone(scenario.threatLevel)}>{scenario.threatLevel}</Badge>}>
      <p className="text-sm text-text-secondary">{scenario.description}</p>
      <div className="mt-3 rounded-md border border-border bg-surface-2 p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">Attack vector</p>
        <p className="mt-1 text-xs leading-relaxed text-text-secondary">{scenario.attackVector}</p>
      </div>
      {scenario.repeated && (
        <p className="mt-2 text-xs text-text-muted">Runs {scenario.attempts} sequential requests against the real API.</p>
      )}
      <button
        type="button"
        onClick={() => onRun(scenario)}
        disabled={anyRunning}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-md border border-status-accent/40 bg-status-accent/15 px-3 py-2 text-sm font-semibold text-text-primary transition-colors hover:enabled:bg-status-accent/25 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isRunning ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            RUNNING...
          </>
        ) : (
          <>
            <Crosshair className="h-4 w-4" aria-hidden="true" />
            RUN SIMULATION
          </>
        )}
      </button>
    </Card>
  )
}
