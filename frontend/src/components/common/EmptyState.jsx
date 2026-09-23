import { Inbox } from 'lucide-react'

export default function EmptyState({ title = 'No data yet', message, icon: Icon = Inbox }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border px-6 py-12 text-center">
      <Icon className="h-7 w-7 text-text-muted" aria-hidden="true" />
      <p className="font-medium text-text-primary">{title}</p>
      {message && <p className="max-w-sm text-sm text-text-muted">{message}</p>}
    </div>
  )
}
