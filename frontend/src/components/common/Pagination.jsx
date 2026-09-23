import { ChevronLeft, ChevronRight } from 'lucide-react'

export default function Pagination({ page, pageCount, onPageChange, totalItems, pageSize }) {
  if (pageCount <= 1) return null

  const start = (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, totalItems)

  return (
    <div className="flex items-center justify-between gap-3 px-1 pt-3 text-xs text-text-muted">
      <span>
        Showing {start}–{end} of {totalItems}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
          className="flex items-center rounded-md border border-border bg-surface-2 p-1.5 disabled:cursor-not-allowed disabled:opacity-40 hover:enabled:bg-surface-3"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </button>
        <span className="px-2 font-medium text-text-secondary">
          Page {page} / {pageCount}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pageCount}
          aria-label="Next page"
          className="flex items-center rounded-md border border-border bg-surface-2 p-1.5 disabled:cursor-not-allowed disabled:opacity-40 hover:enabled:bg-surface-3"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
