import { useMemo, useState } from 'react'
import { Info } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getAlerts, getDashboard, getSecurityEvents, getUsers, submitAccessRequest } from '../services/api'
import { SCENARIOS } from '../data/simulationScenarios'
import Card from '../components/common/Card'
import EmptyState from '../components/common/EmptyState'
import ScenarioCard from '../components/security/ScenarioCard'
import SimulationResultPanel from '../components/security/SimulationResultPanel'
import DecisionBadge from '../components/security/DecisionBadge'
import RiskBadge from '../components/security/RiskBadge'
import { TableShell } from '../components/tables/TableShell'
import { formatDateTime } from '../utils/formatting'

const HISTORY_LIMIT = 25
const EVENT_LOOKUP_LIMIT = 20

export default function Simulator() {
  const usersQuery = useApi(getUsers)
  const dashboardQuery = useApi(getDashboard)

  const [runningId, setRunningId] = useState(null)
  const [results, setResults] = useState({})
  const [activeScenarioId, setActiveScenarioId] = useState(null)
  const [history, setHistory] = useState([])

  const roleByUsername = useMemo(() => {
    const map = {}
    for (const user of usersQuery.data || []) map[user.username] = user.role
    return map
  }, [usersQuery.data])

  function addHistoryEntry(scenario, response) {
    setHistory((prev) =>
      [
        {
          id: `${response.request_id}-${response.timestamp}`,
          timestamp: response.timestamp,
          scenarioName: scenario.name,
          user: scenario.requestPayload.user,
          resource: scenario.requestPayload.resource,
          riskScore: response.risk_score,
          riskLevel: response.risk_level,
          decision: response.decision,
        },
        ...prev,
      ].slice(0, HISTORY_LIMIT)
    )
  }

  async function confirmEventAndAlert(requestId) {
    const [events, alerts] = await Promise.all([
      getSecurityEvents(EVENT_LOOKUP_LIMIT),
      getAlerts(EVENT_LOOKUP_LIMIT),
    ])
    return {
      securityEvent: events.find((event) => event.access_request_id === requestId),
      alert: alerts.find((alert) => alert.access_request_id === requestId),
    }
  }

  async function runScenario(scenario) {
    setRunningId(scenario.id)
    setActiveScenarioId(scenario.id)
    setResults((prev) => ({ ...prev, [scenario.id]: { status: 'running' } }))

    try {
      if (scenario.repeated) {
        const attempts = []
        for (let attemptNumber = 1; attemptNumber <= scenario.attempts; attemptNumber += 1) {
          // Sequential on purpose: the backend's repeated-failure window is
          // time-based, so attempts must actually happen one after another.
          // eslint-disable-next-line no-await-in-loop
          const response = await submitAccessRequest(scenario.requestPayload)
          attempts.push({ attemptNumber, response })
          addHistoryEntry(scenario, response)
        }
        const last = attempts[attempts.length - 1]
        const { securityEvent, alert } = await confirmEventAndAlert(last.response.request_id)
        setResults((prev) => ({ ...prev, [scenario.id]: { status: 'success', attempts, securityEvent, alert } }))
      } else {
        const response = await submitAccessRequest(scenario.requestPayload)
        addHistoryEntry(scenario, response)
        const { securityEvent, alert } = await confirmEventAndAlert(response.request_id)
        setResults((prev) => ({ ...prev, [scenario.id]: { status: 'success', response, securityEvent, alert } }))
      }
    } catch (err) {
      setResults((prev) => ({ ...prev, [scenario.id]: { status: 'error', message: err.message } }))
    } finally {
      setRunningId(null)
      dashboardQuery.reload()
    }
  }

  const activeScenario = SCENARIOS.find((s) => s.id === activeScenarioId)
  const activeResult = activeScenarioId ? results[activeScenarioId] : null

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-text-primary">ATTACK SIMULATION LAB</h2>
        <p className="text-sm text-text-muted">Controlled simulation of context-aware cloud access attacks</p>
      </div>

      <div className="flex items-start gap-2 rounded-lg border border-status-info/30 bg-status-info-bg px-4 py-3 text-sm text-text-secondary">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-status-info" aria-hidden="true" />
        <p>
          All scenarios run locally against the CloudContextGuard policy engine. No real cloud infrastructure is
          accessed. Every result below is the live response from <code className="font-mono text-text-primary">POST /api/access/request</code>.
        </p>
      </div>

      {dashboardQuery.data && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MiniMetric label="Total Requests" value={dashboardQuery.data.total_requests} />
          <MiniMetric label="Denied" value={dashboardQuery.data.denied_requests} />
          <MiniMetric label="High Risk" value={dashboardQuery.data.high_risk_requests} />
          <MiniMetric label="Open Alerts" value={dashboardQuery.data.open_alerts} />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {SCENARIOS.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            onRun={runScenario}
            isRunning={runningId === scenario.id}
            anyRunning={Boolean(runningId)}
          />
        ))}
      </div>

      {activeScenario && activeResult && (
        <SimulationResultPanel
          scenario={activeScenario}
          role={roleByUsername[activeScenario.requestPayload.user]}
          result={activeResult}
          onRetry={() => runScenario(activeScenario)}
        />
      )}

      <Card title="Recent Simulations" subtitle="Live results from this session, sourced directly from the API">
        {history.length === 0 ? (
          <EmptyState title="No simulations run yet" message="Run a scenario above to see its real backend result here." />
        ) : (
          <TableShell>
            <thead>
              <tr>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Time</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Scenario</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">User</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Resource</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Risk</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Decision</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.id} className="border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60">
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{formatDateTime(entry.timestamp)}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-primary">{entry.scenarioName}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{entry.user}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{entry.resource}</td>
                  <td className="whitespace-nowrap px-3 py-2.5">
                    <RiskBadge level={entry.riskLevel} score={entry.riskScore} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5">
                    <DecisionBadge decision={entry.decision} />
                  </td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </Card>
    </div>
  )
}

function MiniMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-border bg-surface-1 p-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-text-primary">{value ?? '—'}</p>
    </div>
  )
}
