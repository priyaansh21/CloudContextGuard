import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useHealthStatus } from '../../hooks/useApi'
import { getHealth } from '../../services/api'

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/access-requests': 'Access Requests',
  '/iam': 'Identity & Access Management',
  '/vpc': 'VPC Security',
  '/storage': 'Storage',
  '/security-events': 'Security Events',
  '/alerts': 'Alerts',
  '/policies': 'Policies',
  '/simulator': 'Attack Simulator',
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const { apiStatus, dbStatus } = useHealthStatus(getHealth)
  const title = PAGE_TITLES[location.pathname] || 'CloudContextGuard'

  return (
    <div className="flex h-screen overflow-hidden bg-surface-0">
      <Sidebar apiStatus={apiStatus} dbStatus={dbStatus} open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation overlay"
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title} apiStatus={apiStatus} onMenuClick={() => setSidebarOpen((v) => !v)} />
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
