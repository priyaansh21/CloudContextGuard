import Badge from '../common/Badge'
import { riskTone } from '../../utils/formatting'

export default function RiskBadge({ level, score }) {
  return (
    <Badge tone={riskTone(level)} dot>
      {level}
      {typeof score === 'number' ? ` (${score})` : ''}
    </Badge>
  )
}
