import { cn } from '../../utils/formatting'

/**
 * A small colored status pill. Pass a `tone` object with { text, bg, border }
 * (see utils/formatting.js helpers) so color usage stays centralized.
 */
export default function Badge({ children, tone, className, dot = false }) {
  const { text, bg, border } = tone || {
    text: 'text-text-secondary',
    bg: 'bg-surface-3',
    border: 'border-border',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        text,
        bg,
        border,
        className
      )}
    >
      {dot && <span className={cn('h-1.5 w-1.5 rounded-full', text.replace('text-', 'bg-'))} />}
      {children}
    </span>
  )
}
