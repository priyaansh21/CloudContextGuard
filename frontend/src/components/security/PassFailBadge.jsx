import { Check, X } from 'lucide-react'
import Badge from '../common/Badge'
import { passFailTone } from '../../utils/formatting'

export default function PassFailBadge({ result }) {
  const pass = result === 'PASS' || result === true
  const Icon = pass ? Check : X
  return (
    <Badge tone={passFailTone(result)}>
      <Icon className="h-3 w-3" aria-hidden="true" />
      {pass ? 'PASS' : 'FAIL'}
    </Badge>
  )
}
