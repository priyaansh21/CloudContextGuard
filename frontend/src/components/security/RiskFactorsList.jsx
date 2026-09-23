export default function RiskFactorsList({ factors }) {
  if (!factors || factors.length === 0) {
    return <p className="text-sm text-text-muted">No risk factors contributed to this request.</p>
  }

  return (
    <ul className="space-y-1.5">
      {factors.map((factor) => (
        <li
          key={factor.name}
          className="flex items-start justify-between gap-3 rounded-md border border-border bg-surface-2 px-3 py-2 text-xs"
        >
          <div>
            <p className="font-medium text-text-primary">{factor.name}</p>
            <p className="text-text-muted">{factor.reason}</p>
          </div>
          <span className="shrink-0 font-mono font-semibold text-status-warning">+{factor.points}</span>
        </li>
      ))}
    </ul>
  )
}
