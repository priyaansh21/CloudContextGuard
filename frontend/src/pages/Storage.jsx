import { useMemo } from 'react'
import { Check, X } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getPolicies, getResources } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import { TableShell } from '../components/tables/TableShell'
import { TableSkeleton } from '../components/common/LoadingState'
import { classificationTone } from '../utils/formatting'

function BoolIcon({ value }) {
  return value ? (
    <Check className="h-4 w-4 text-status-safe" aria-label="Yes" />
  ) : (
    <X className="h-4 w-4 text-text-muted" aria-label="No" />
  )
}

export default function Storage() {
  const resources = useApi(getResources)
  const policies = useApi(getPolicies)
  const { data, loading, error, reload } = resources

  // The authoritative "required role" for a resource lives on its active
  // policy (Policy.required_role), not on Resource.required_role - that
  // field is never set by the seed data. Join by resource name rather than
  // duplicating the value into the resources endpoint.
  const requiredRoleByResource = useMemo(() => {
    const map = {}
    for (const policy of policies.data || []) {
      if (!policy.resource) continue
      if (map[policy.resource] && !policy.is_enabled) continue
      map[policy.resource] = policy.required_role
    }
    return map
  }, [policies.data])

  if (error || policies.error) {
    return (
      <ErrorState
        message={(error || policies.error).message}
        onRetry={() => {
          resources.reload()
          policies.reload()
        }}
      />
    )
  }

  return (
    <Card title="Protected Resources" subtitle="Storage and data resources under context-aware access control">
      {loading || policies.loading ? (
        <TableSkeleton rows={4} cols={6} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No resources found" message="Seed the database to populate the resource catalog." />
      ) : (
        <TableShell>
          <thead>
            <tr>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Resource</th>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Classification</th>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Required Role</th>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Trusted VPC</th>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">MFA</th>
              <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">External Access</th>
            </tr>
          </thead>
          <tbody>
            {data.map((resource) => (
              <tr key={resource.id} className="border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60">
                <td className="whitespace-nowrap px-3 py-2.5">
                  <p className="font-medium text-text-primary">{resource.name}</p>
                  <p className="text-xs text-text-muted">{resource.resource_type}</p>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <Badge tone={classificationTone(resource.classification)}>{resource.classification || 'UNSPECIFIED'}</Badge>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">
                  {requiredRoleByResource[resource.name] || 'Not specified'}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">
                  {resource.trusted_vpc ? resource.trusted_vpc_name || 'Required' : <BoolIcon value={false} />}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <BoolIcon value={resource.mfa_required} />
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <BoolIcon value={resource.external_access_allowed} />
                </td>
              </tr>
            ))}
          </tbody>
        </TableShell>
      )}
    </Card>
  )
}
