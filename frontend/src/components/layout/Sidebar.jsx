import { NavLink } from 'react-router-dom'
import {
  Bell,
  Crosshair,
  Database,
  FileText,
  LayoutDashboard,
  ListChecks,
  Network,
  Shield,
  ShieldAlert,
  Users,
} from 'lucide-react'
import { cn } from '../../utils/formatting'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/access-requests', label: 'Access Requests', icon: ListChecks },
  { to: '/iam', label: 'IAM', icon: Users },
  { to: '/vpc', label: 'VPC Security', icon: Network },
  { to: '/storage', label: 'Storage', icon: Database },
  { to: '/security-events', label: 'Security Events', icon: ShieldAlert },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/policies', label: 'Policies', icon: FileText },
  { to: '/simulator', label: 'Attack Simulator', icon: Crosshair },
]

function StatusRow({ label, value, healthy }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-text-muted">{label}</span>
      <span className={cn('flex items-center gap-1.5 font-medium', healthy ? 'text-status-safe' : 'text-status-critical')}>
        <span className={cn('h-1.5 w-1.5 rounded-full', healthy ? 'bg-status-safe' : 'bg-status-critical')} />
        {value}
      </span>
    </div>
  )
}

export default function Sidebar({ apiStatus, dbStatus, open, onNavigate }) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-surface-1 transition-transform lg:static lg:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="flex items-center gap-2 border-b border-border-subtle px-5 py-4">
        <Shield className="h-6 w-6 text-status-info" aria-hidden="true" />
        <div>
          <p className="text-sm font-bold leading-tight text-text-primary">CloudContextGuard</p>
          <p className="text-[11px] leading-tight text-text-muted">Security Console</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Primary navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-status-accent/15 text-text-primary border border-status-accent/30'
                  : 'text-text-secondary hover:bg-surface-2 hover:text-text-primary border border-transparent'
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="space-y-2 border-t border-border-subtle px-5 py-4">
        <StatusRow label="API Status" value={apiStatus} healthy={apiStatus === 'ONLINE'} />
        <StatusRow label="Database" value={dbStatus} healthy={dbStatus === 'CONNECTED'} />
      </div>
    </aside>
  )
}
