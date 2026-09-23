/** Formatting and small display helpers shared across pages/components. */

export function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value.endsWith?.('Z') ? value : `${value}Z`)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatRelativeTime(value) {
  if (!value) return '—'
  const date = new Date(value.endsWith?.('Z') ? value : `${value}Z`)
  if (Number.isNaN(date.getTime())) return String(value)
  const diffMs = Date.now() - date.getTime()
  const diffSec = Math.round(diffMs / 1000)
  if (diffSec < 5) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.round(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHour = Math.round(diffMin / 60)
  if (diffHour < 24) return `${diffHour}h ago`
  const diffDay = Math.round(diffHour / 24)
  return `${diffDay}d ago`
}

/** Tailwind class fragments for each decision value. */
export function decisionTone(decision) {
  if (decision === 'ALLOW') {
    return { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
  }
  if (decision === 'DENY') {
    return { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
  }
  return { text: 'text-text-secondary', bg: 'bg-surface-3', border: 'border-border' }
}

/** Tailwind class fragments for each risk/severity level. */
export function riskTone(level) {
  switch ((level || '').toUpperCase()) {
    case 'LOW':
      return { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
    case 'MEDIUM':
      return { text: 'text-status-info', bg: 'bg-status-info-bg', border: 'border-status-info/30' }
    case 'HIGH':
      return { text: 'text-status-warning', bg: 'bg-status-warning-bg', border: 'border-status-warning/30' }
    case 'CRITICAL':
      return { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
    default:
      return { text: 'text-text-secondary', bg: 'bg-surface-3', border: 'border-border' }
  }
}

export function passFailTone(result) {
  if (result === 'PASS' || result === true) {
    return { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
  }
  return { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
}

export function classificationTone(classification) {
  switch ((classification || '').toUpperCase()) {
    case 'PUBLIC':
      return { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
    case 'INTERNAL':
      return { text: 'text-status-info', bg: 'bg-status-info-bg', border: 'border-status-info/30' }
    case 'CONFIDENTIAL':
      return { text: 'text-status-warning', bg: 'bg-status-warning-bg', border: 'border-status-warning/30' }
    case 'RESTRICTED':
      return { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
    default:
      return { text: 'text-text-secondary', bg: 'bg-surface-3', border: 'border-border' }
  }
}

export function statusTone(status) {
  switch ((status || '').toUpperCase()) {
    case 'OPEN':
      return { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
    case 'ACKNOWLEDGED':
      return { text: 'text-status-warning', bg: 'bg-status-warning-bg', border: 'border-status-warning/30' }
    case 'RESOLVED':
      return { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
    default:
      return { text: 'text-text-secondary', bg: 'bg-surface-3', border: 'border-border' }
  }
}

export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}
