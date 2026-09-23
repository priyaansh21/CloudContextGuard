import { ArrowDown, Lock, Network, ShieldCheck } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getVpcs } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import { CardSkeletonGrid } from '../components/common/LoadingState'

export default function VPCSecurity() {
  const { data, loading, error, reload } = useApi(getVpcs)

  if (error) return <ErrorState message={error.message} onRetry={reload} />

  const trustedCount = data ? data.filter((v) => v.is_trusted).length : 0
  const untrustedCount = data ? data.filter((v) => !v.is_trusted).length : 0

  return (
    <div className="space-y-6">
      <Card title="Network Boundary Model" subtitle="How a request's origin is evaluated against a resource's trust requirement">
        <div className="mx-auto flex max-w-xs flex-col items-center gap-1 text-center">
          <div className="w-full rounded-md border border-status-critical/30 bg-status-critical-bg px-4 py-2.5 text-sm font-semibold text-status-critical">
            EXTERNAL NETWORK
          </div>
          <ArrowDown className="h-5 w-5 text-text-muted" aria-hidden="true" />
          <div className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-surface-2 px-4 py-2.5 text-sm font-semibold text-text-primary">
            <Network className="h-4 w-4 text-status-info" aria-hidden="true" />
            POLICY EVALUATION
          </div>
          <ArrowDown className="h-5 w-5 text-text-muted" aria-hidden="true" />
          <div className="w-full rounded-lg border-2 border-status-safe/40 bg-status-safe-bg px-4 py-4">
            <p className="flex items-center justify-center gap-2 text-sm font-bold text-status-safe">
              <Lock className="h-4 w-4" aria-hidden="true" />
              TRUSTED VPC
            </p>
            <p className="mt-1 text-xs text-text-secondary">Protected Resources</p>
          </div>
        </div>
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text-primary">
          Virtual Private Clouds {data ? `(${trustedCount} trusted, ${untrustedCount} untrusted)` : ''}
        </h2>
        {loading ? (
          <CardSkeletonGrid count={4} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No VPCs configured" message="Seed the database to populate the network catalog." />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {data.map((vpc) => (
              <div key={vpc.id} className="rounded-lg border border-border bg-surface-1 p-4">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-mono text-sm font-semibold text-text-primary">{vpc.name}</p>
                  <Badge
                    tone={
                      vpc.is_trusted
                        ? { text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }
                        : { text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }
                    }
                  >
                    {vpc.is_trusted ? <ShieldCheck className="h-3 w-3" aria-hidden="true" /> : null}
                    {vpc.is_trusted ? 'TRUSTED' : 'UNTRUSTED'}
                  </Badge>
                </div>
                <p className="mt-2 font-mono text-xs text-text-muted">{vpc.cidr}</p>
                <p className="mt-1 text-xs text-text-secondary">Trust level: {vpc.trust_level || 'n/a'}</p>
                <p className="mt-2 text-xs leading-relaxed text-text-muted">{vpc.description || 'No description provided.'}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
