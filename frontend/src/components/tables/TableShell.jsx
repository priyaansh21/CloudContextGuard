import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '../../utils/formatting'

/** Consistent table chrome: horizontal scroll container + sortable headers. */
export function TableShell({ children }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-max border-collapse text-left text-sm">{children}</table>
    </div>
  )
}

export function SortableHeader({ label, sortKey, activeSort, onSort, className }) {
  const isActive = activeSort?.key === sortKey
  return (
    <th scope="col" className={cn('bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted', className)}>
      {onSort ? (
        <button
          type="button"
          onClick={() => onSort(sortKey)}
          className="flex items-center gap-1 hover:text-text-primary"
        >
          {label}
          {isActive &&
            (activeSort.direction === 'asc' ? (
              <ChevronUp className="h-3 w-3" aria-hidden="true" />
            ) : (
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            ))}
        </button>
      ) : (
        label
      )}
    </th>
  )
}
