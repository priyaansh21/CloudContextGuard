import { AlertOctagon, Bell, ListChecks, ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react'
import { Database, KeyRound, Network, ScrollText } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getDashboard } from '../services/api'
import MetricCard from '../components/dashboard/MetricCard'
import PostureCard from '../components/dashboard/PostureCard'
import DecisionChart from '../components/dashboard/DecisionChart'
import RiskChart from '../components/dashboard/RiskChart'
import DistributionBarChart from '../components/dashboard/DistributionBarChart'
import RecentEventsPanel from '../components/dashboard/RecentEventsPanel'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import { CardSkeletonGrid, Skeleton } from '../components/common/LoadingState'

export default function Dashboard() {
  const { data, loading, error, reload } = useApi(getDashboard)

  if (error) return <ErrorState message={error.message} onRetry={reload} />

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <CardSkeletonGrid count={6} />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          label="Total Requests"
          value={data.total_requests}
          icon={ListChecks}
          tone={{ text: 'text-status-info', bg: 'bg-status-info-bg' }}
        />
        <MetricCard
          label="Allowed"
          value={data.allowed_requests}
          icon={ShieldCheck}
          tone={{ text: 'text-status-safe', bg: 'bg-status-safe-bg' }}
        />
        <MetricCard
          label="Denied"
          value={data.denied_requests}
          icon={ShieldX}
          tone={{ text: 'text-status-critical', bg: 'bg-status-critical-bg' }}
        />
        <MetricCard
          label="High Risk"
          value={data.high_risk_requests}
          icon={AlertOctagon}
          tone={{ text: 'text-status-warning', bg: 'bg-status-warning-bg' }}
        />
        <MetricCard
          label="Critical Events"
          value={data.critical_events}
          icon={ShieldAlert}
          tone={{ text: 'text-status-critical', bg: 'bg-status-critical-bg' }}
        />
        <MetricCard
          label="Open Alerts"
          value={data.open_alerts}
          icon={Bell}
          tone={{ text: 'text-status-warning', bg: 'bg-status-warning-bg' }}
        />
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text-primary">Security Posture</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <PostureCard
            title="IAM"
            status="ACTIVE"
            description="Role-based authorization enabled across all identities and resources."
            icon={KeyRound}
          />
          <PostureCard
            title="VPC"
            status={data.protected_resources > 0 ? 'PROTECTED' : 'ACTIVE'}
            description={`Trusted network boundaries enforced on ${data.protected_resources} protected resource(s).`}
            icon={Network}
          />
          <PostureCard
            title="STORAGE"
            status={data.protected_resources > 0 ? 'PROTECTED' : 'ACTIVE'}
            description={`Context-aware access control applied to ${data.protected_resources} storage resource(s).`}
            icon={Database}
          />
          <PostureCard
            title="POLICY ENGINE"
            status="ACTIVE"
            description={`Real-time policy evaluation enabled — ${data.total_requests} request(s) evaluated.`}
            icon={ScrollText}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card title="Access Decisions" subtitle="ALLOW vs DENY">
          <DecisionChart distribution={data.decision_distribution} />
        </Card>
        <Card title="Risk Distribution" subtitle="LOW · MEDIUM · HIGH · CRITICAL">
          <RiskChart distribution={data.risk_distribution} />
        </Card>
        <Card title="Requests by VPC">
          <DistributionBarChart
            distribution={data.requests_by_vpc}
            color="#38bdf8"
            emptyTitle="No VPC data yet"
            emptyMessage="Network origins appear once requests are submitted."
          />
        </Card>
        <Card title="Requests by User">
          <DistributionBarChart
            distribution={data.requests_by_user}
            color="#6366f1"
            emptyTitle="No user activity yet"
            emptyMessage="User activity appears once requests are submitted."
          />
        </Card>
      </div>

      <Card title="Recent Security Events">
        <RecentEventsPanel events={data.recent_events} />
      </Card>
    </div>
  )
}
