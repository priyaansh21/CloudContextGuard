export default function SelectFilter({ label, value, onChange, options }) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-text-muted">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
        className="rounded-md border border-border bg-surface-2 py-1.5 pl-2 pr-7 text-sm text-text-primary focus:border-status-info focus:outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}
