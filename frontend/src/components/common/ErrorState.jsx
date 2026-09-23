import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-status-critical/30 bg-status-critical-bg px-6 py-12 text-center">
      <AlertTriangle className="h-8 w-8 text-status-critical" aria-hidden="true" />
      <div>
        <p className="font-semibold text-text-primary">CloudContextGuard API is unavailable.</p>
        {message && <p className="mt-1 text-sm text-text-secondary">{message}</p>}
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 inline-flex items-center gap-2 rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-3"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  )
}
