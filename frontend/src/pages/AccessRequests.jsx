import { useMemo, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { getAccessRequests } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import { TableSkeleton } from '../components/common/LoadingState'
import SearchInput from '../components/common/SearchInput'
import SelectFilter from '../components/common/SelectFilter'
import Pagination from '../components/common/Pagination'
import { TableShell, SortableHeader } from '../components/tables/TableShell'
import DecisionBadge from '../components/security/DecisionBadge'
import RiskBadge from '../components/security/RiskBadge'
import AccessRequestDetailModal from '../components/security/AccessRequestDetailModal'
import { formatDateTime } from '../utils/formatting'

const DECISION_OPTIONS = [
  { value: 'ALL', label: 'All decisions' },
  { value: 'ALLOW', label: 'ALLOW' },
  { value: 'DENY', label: 'DENY' },
]
const RISK_OPTIONS = [
  { value: 'ALL', label: 'All risk levels' },
  { value: 'LOW', label: 'LOW' },
  { value: 'MEDIUM', label: 'MEDIUM' },
  { value: 'HIGH', label: 'HIGH' },
  { value: 'CRITICAL', label: 'CRITICAL' },
]
const PAGE_SIZE = 15

export default function AccessRequests() {
  const { data, loading, error, reload } = useApi(getAccessRequests)
  const [search, setSearch] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('ALL')
  const [riskFilter, setRiskFilter] = useState('ALL')
  const [vpcFilter, setVpcFilter] = useState('ALL')
  const [sort, setSort] = useState({ key: 'timestamp', direction: 'desc' })
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState(null)

  const vpcOptions = useMemo(() => {
    const unique = Array.from(new Set((data || []).map((r) => r.source_vpc).filter(Boolean)))
    return [{ value: 'ALL', label: 'All VPCs' }, ...unique.map((v) => ({ value: v, label: v }))]
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    const query = search.trim().toLowerCase()
    return data.filter((row) => {
      if (decisionFilter !== 'ALL' && row.final_decision !== decisionFilter) return false
      if (riskFilter !== 'ALL' && row.risk_level !== riskFilter) return false
      if (vpcFilter !== 'ALL' && row.source_vpc !== vpcFilter) return false
      if (!query) return true
      const haystack = [row.user, row.role, row.action, row.resource, row.source_ip, row.source_vpc]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(query)
    })
  }, [data, search, decisionFilter, riskFilter, vpcFilter])

  const sorted = useMemo(() => {
    const rows = [...filtered]
    const { key, direction } = sort
    rows.sort((a, b) => {
      let av = a[key]
      let bv = b[key]
      if (key === 'timestamp') {
        av = new Date(av).getTime()
        bv = new Date(bv).getTime()
      }
      if (av == null) av = ''
      if (bv == null) bv = ''
      if (av < bv) return direction === 'asc' ? -1 : 1
      if (av > bv) return direction === 'asc' ? 1 : -1
      return 0
    })
    return rows
  }, [filtered, sort])

  const pageCount = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const pageRows = sorted.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  function handleSort(key) {
    setSort((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }

  function updateFilterAndResetPage(setter) {
    return (value) => {
      setter(value)
      setPage(1)
    }
  }

  if (error) return <ErrorState message={error.message} onRetry={reload} />

  return (
    <div className="space-y-4">
      <Card
        title="Access Request Audit Log"
        subtitle={data ? `${sorted.length} of ${data.length} requests` : undefined}
      >
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="min-w-[220px] flex-1">
            <SearchInput
              value={search}
              onChange={updateFilterAndResetPage(setSearch)}
              placeholder="Search user, action, resource, IP..."
            />
          </div>
          <SelectFilter label="Decision" value={decisionFilter} onChange={updateFilterAndResetPage(setDecisionFilter)} options={DECISION_OPTIONS} />
          <SelectFilter label="Risk" value={riskFilter} onChange={updateFilterAndResetPage(setRiskFilter)} options={RISK_OPTIONS} />
          <SelectFilter label="VPC" value={vpcFilter} onChange={updateFilterAndResetPage(setVpcFilter)} options={vpcOptions} />
        </div>

        {loading ? (
          <TableSkeleton rows={8} cols={9} />
        ) : sorted.length === 0 ? (
          <EmptyState
            title="No access requests found"
            message={data && data.length > 0 ? 'Try adjusting your filters.' : 'Submit a request via the API to populate this log.'}
          />
        ) : (
          <>
            <TableShell>
              <thead>
                <tr>
                  <SortableHeader label="Time" sortKey="timestamp" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="User" sortKey="user" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Role" sortKey="role" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Action" sortKey="action" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Resource" sortKey="resource" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Source IP" sortKey="source_ip" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="VPC" sortKey="source_vpc" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Risk" sortKey="risk_score" activeSort={sort} onSort={handleSort} />
                  <SortableHeader label="Decision" sortKey="final_decision" activeSort={sort} onSort={handleSort} />
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => setSelected(row)}
                    tabIndex={0}
                    role="button"
                    aria-label={`View details for access request ${row.id}`}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') setSelected(row)
                    }}
                    className="cursor-pointer border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60 hover:bg-surface-3"
                  >
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{formatDateTime(row.timestamp)}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 font-medium text-text-primary">{row.user || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{row.role || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{row.action}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{row.resource || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{row.source_ip || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{row.source_vpc || '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <RiskBadge level={row.risk_level} score={row.risk_score} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <DecisionBadge decision={row.final_decision} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </TableShell>
            <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} totalItems={sorted.length} pageSize={PAGE_SIZE} />
          </>
        )}
      </Card>

      <AccessRequestDetailModal request={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
