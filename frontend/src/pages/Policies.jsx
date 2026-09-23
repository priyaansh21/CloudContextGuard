import { useMemo, useState } from 'react'
import { AlertTriangle, Check, Eye, Pencil, X } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getPolicies, getResources } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import { TableShell } from '../components/tables/TableShell'
import { TableSkeleton } from '../components/common/LoadingState'
import PolicyDetailModal from '../components/security/PolicyDetailModal'
import PolicyEditorModal from '../components/security/PolicyEditorModal'
import { formatDateTime } from '../utils/formatting'

const SENSITIVE_CLASSIFICATIONS = ['CONFIDENTIAL', 'RESTRICTED']

function BoolIcon({ value }) {
  return value ? (
    <Check className="h-4 w-4 text-status-safe" aria-label="Yes" />
  ) : (
    <X className="h-4 w-4 text-text-muted" aria-label="No" />
  )
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-lg border border-border bg-surface-1 p-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-xl font-bold text-text-primary">{value}</p>
    </div>
  )
}

export default function Policies() {
  const policiesQuery = useApi(getPolicies)
  const resourcesQuery = useApi(getResources)
  const [viewingPolicy, setViewingPolicy] = useState(null)
  const [editingPolicy, setEditingPolicy] = useState(null)

  const data = policiesQuery.data

  const classificationByResource = useMemo(() => {
    const map = {}
    for (const resource of resourcesQuery.data || []) map[resource.name] = resource.classification
    return map
  }, [resourcesQuery.data])

  const summary = useMemo(() => {
    if (!data) return null
    return {
      total: data.length,
      enabled: data.filter((p) => p.is_enabled).length,
      mfaProtected: data.filter((p) => p.mfa_required).length,
      externalAccess: data.filter((p) => p.external_access_allowed).length,
      highRisk: data.filter(
        (p) => p.external_access_allowed && SENSITIVE_CLASSIFICATIONS.includes(classificationByResource[p.resource])
      ).length,
    }
  }, [data, classificationByResource])

  if (policiesQuery.error) return <ErrorState message={policiesQuery.error.message} onRetry={policiesQuery.reload} />

  return (
    <div className="space-y-4">
      {summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <SummaryCard label="Total Policies" value={summary.total} />
          <SummaryCard label="Enabled" value={summary.enabled} />
          <SummaryCard label="MFA Protected" value={summary.mfaProtected} />
          <SummaryCard label="External Access" value={summary.externalAccess} />
          <SummaryCard label="High-Risk" value={summary.highRisk} />
        </div>
      )}

      <Card title="Resource Policies" subtitle="Configured security requirements evaluated by the policy engine - editable, database-backed">
        {policiesQuery.loading ? (
          <TableSkeleton rows={4} cols={9} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No policies configured" message="Seed the database to populate resource policies." />
        ) : (
          <TableShell>
            <thead>
              <tr>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Policy</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Resource</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Required Role</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Trusted VPC</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">MFA</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Max Risk</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">External Access</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Status</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Updated</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((policy) => {
                const showWarning =
                  policy.external_access_allowed && SENSITIVE_CLASSIFICATIONS.includes(classificationByResource[policy.resource])
                return (
                  <tr key={policy.id} className="border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60">
                    <td className="px-3 py-2.5">
                      <p className="font-medium text-text-primary">{policy.name}</p>
                      <p className="max-w-xs text-xs text-text-muted">{policy.description || 'No description'}</p>
                      {showWarning && (
                        <p className="mt-1 flex items-center gap-1 text-[11px] font-medium text-status-warning">
                          <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                          External access enabled on sensitive resource.
                        </p>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{policy.resource || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{policy.required_role || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{policy.trusted_vpc || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <BoolIcon value={policy.mfa_required} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{policy.max_risk_score ?? '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <BoolIcon value={policy.external_access_allowed} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <Badge
                        tone={
                          policy.is_enabled
                            ? { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
                            : { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
                        }
                      >
                        {policy.is_enabled ? 'ENABLED' : 'DISABLED'}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{formatDateTime(policy.updated_at)}</td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setViewingPolicy(policy)}
                          aria-label={`View policy ${policy.name}`}
                          className="flex items-center gap-1 rounded-md border border-border bg-surface-2 px-2 py-1 text-xs font-medium text-text-secondary hover:bg-surface-3"
                        >
                          <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingPolicy(policy)}
                          aria-label={`Edit policy ${policy.name}`}
                          className="flex items-center gap-1 rounded-md border border-status-accent/40 bg-status-accent/15 px-2 py-1 text-xs font-medium text-text-primary hover:bg-status-accent/25"
                        >
                          <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </TableShell>
        )}
      </Card>

      <PolicyDetailModal policy={viewingPolicy} onClose={() => setViewingPolicy(null)} />
      {editingPolicy && (
        <PolicyEditorModal
          policy={editingPolicy}
          onClose={() => setEditingPolicy(null)}
          onSaved={() => {
            policiesQuery.reload()
          }}
        />
      )}
    </div>
  )
}
