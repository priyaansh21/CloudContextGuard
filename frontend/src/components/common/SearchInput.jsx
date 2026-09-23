import { Search } from 'lucide-react'

export default function SearchInput({ value, onChange, placeholder = 'Search...', ariaLabel }) {
  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" aria-hidden="true" />
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={ariaLabel || placeholder}
        className="w-full rounded-md border border-border bg-surface-2 py-1.5 pl-8 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-status-info focus:outline-none"
      />
    </div>
  )
}
