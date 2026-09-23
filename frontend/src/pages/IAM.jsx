import { useMemo } from 'react'
import { ShieldCheck, ShieldOff } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getPermissions, getRoles, getUsers } from '../services/api'
import Card from '../components/common/Card'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import { TableShell } from '../components/tables/TableShell'
import { TableSkeleton } from '../components/common/LoadingState'
import { formatDateTime } from '../utils/formatting'

export default function IAM() {
  const users = useApi(getUsers)
  const roles = useApi(getRoles)
  const permissions = useApi(getPermissions)

  const permissionsByRole = useMemo(() => {
    const map = {}
    for (const permission of permissions.data || []) {
      const key = permission.role || 'Unassigned'
      map[key] = map[key] || []
      map[key].push(permission)
    }
    return map
  }, [permissions.data])

  const anyError = users.error || roles.error || permissions.error
  if (anyError) {
    return (
      <ErrorState
        message={anyError.message}
        onRetry={() => {
          users.reload()
          roles.reload()
          permissions.reload()
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <Card title="Users" subtitle="Simulated identities used to generate access requests">
        {users.loading ? (
          <TableSkeleton rows={4} cols={4} />
        ) : !users.data || users.data.length === 0 ? (
          <EmptyState title="No users found" message="Seed the database to populate the identity catalog." />
        ) : (
          <TableShell>
            <thead>
              <tr>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Username</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Display Name</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Role</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Status</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.data.map((user) => (
                <tr key={user.id} className="border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60">
                  <td className="whitespace-nowrap px-3 py-2.5 font-medium text-text-primary">{user.username}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{user.display_name || '—'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{user.role || 'Unassigned'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5">
                    {user.is_active ? (
                      <Badge tone={{ text: 'text-status-safe', bg: 'bg-status-safe-bg', border: 'border-status-safe/30' }}>
                        <ShieldCheck className="h-3 w-3" aria-hidden="true" /> Active
                      </Badge>
                    ) : (
                      <Badge tone={{ text: 'text-status-critical', bg: 'bg-status-critical-bg', border: 'border-status-critical/30' }}>
                        <ShieldOff className="h-3 w-3" aria-hidden="true" /> Inactive
                      </Badge>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-text-secondary">{formatDateTime(user.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </Card>

      <Card title="Roles" subtitle="Each role's granted permissions">
        {roles.loading ? (
          <TableSkeleton rows={4} cols={2} />
        ) : !roles.data || roles.data.length === 0 ? (
          <EmptyState title="No roles found" />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {roles.data.map((role) => (
              <div key={role.id} className="rounded-lg border border-border bg-surface-2 p-4">
                <p className="text-sm font-semibold text-text-primary">{role.name}</p>
                <p className="mt-1 text-xs text-text-muted">{role.description || 'No description provided.'}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {(permissionsByRole[role.name] || []).map((permission) => (
                    <span
                      key={permission.id}
                      className="rounded-md border border-border bg-surface-3 px-2 py-0.5 font-mono text-[11px] text-text-secondary"
                    >
                      {permission.action}:{permission.resource_pattern}
                    </span>
                  ))}
                  {(permissionsByRole[role.name] || []).length === 0 && (
                    <span className="text-xs text-text-muted">No permissions granted.</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Permissions">
        {permissions.loading ? (
          <TableSkeleton rows={6} cols={3} />
        ) : !permissions.data || permissions.data.length === 0 ? (
          <EmptyState title="No permissions found" />
        ) : (
          <TableShell>
            <thead>
              <tr>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Role</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Action</th>
                <th className="bg-surface-2 px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Resource Pattern</th>
              </tr>
            </thead>
            <tbody>
              {permissions.data.map((permission) => (
                <tr key={permission.id} className="border-t border-border-subtle odd:bg-surface-1 even:bg-surface-1/60">
                  <td className="whitespace-nowrap px-3 py-2.5 font-medium text-text-primary">{permission.role || 'Unassigned'}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 font-mono text-text-secondary">{permission.action}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 font-mono text-text-secondary">{permission.resource_pattern}</td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </Card>
    </div>
  )
}
