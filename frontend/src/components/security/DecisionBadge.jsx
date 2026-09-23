import { ShieldCheck, ShieldX } from 'lucide-react'
import Badge from '../common/Badge'
import { decisionTone } from '../../utils/formatting'

export default function DecisionBadge({ decision }) {
  const Icon = decision === 'ALLOW' ? ShieldCheck : ShieldX
  return (
    <Badge tone={decisionTone(decision)}>
      <Icon className="h-3 w-3" aria-hidden="true" />
      {decision}
    </Badge>
  )
}
