import { Menu, Wifi, WifiOff } from 'lucide-react'
import { cn } from '../../utils/formatting'

export default function TopBar({ title, apiStatus, onMenuClick }) {
  const online = apiStatus === 'ONLINE'
  const checking = apiStatus === 'CHECKING'

  return (
    <header className="flex items-center justify-between gap-3 border-b border-border bg-surface-1 px-4 py-3 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Toggle navigation menu"
          className="rounded-md p-1.5 text-text-secondary hover:bg-surface-2 lg:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <div className="min-w-0">
          <h1 className="truncate text-base font-semibold text-text-primary">{title}</h1>
          <p className="truncate text-xs text-text-muted">Context-Aware Cloud Security</p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <span className="hidden rounded-full border border-border bg-surface-2 px-2.5 py-1 text-[11px] font-semibold tracking-wide text-text-muted sm:inline-block">
          LOCAL SIMULATION
        </span>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold',
            checking
              ? 'border-border text-text-muted bg-surface-2'
              : online
                ? 'border-status-safe/30 bg-status-safe-bg text-status-safe'
                : 'border-status-critical/30 bg-status-critical-bg text-status-critical'
          )}
        >
          {online ? <Wifi className="h-3.5 w-3.5" aria-hidden="true" /> : <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />}
          {checking ? 'CHECKING' : online ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
    </header>
  )
}
