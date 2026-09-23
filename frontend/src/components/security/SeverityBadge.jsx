import Badge from '../common/Badge'
import { riskTone } from '../../utils/formatting'

/** Severity uses the same LOW/MEDIUM/HIGH/CRITICAL palette as risk. */
export default function SeverityBadge({ severity }) {
  return (
    <Badge tone={riskTone(severity)} dot>
      {severity}
    </Badge>
  )
}
