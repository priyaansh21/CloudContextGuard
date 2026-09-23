import { Route, BrowserRouter, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import AccessRequests from './pages/AccessRequests'
import IAM from './pages/IAM'
import VPCSecurity from './pages/VPCSecurity'
import Storage from './pages/Storage'
import SecurityEvents from './pages/SecurityEvents'
import Alerts from './pages/Alerts'
import Policies from './pages/Policies'
import Simulator from './pages/Simulator'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/access-requests" element={<AccessRequests />} />
          <Route path="/iam" element={<IAM />} />
          <Route path="/vpc" element={<VPCSecurity />} />
          <Route path="/storage" element={<Storage />} />
          <Route path="/security-events" element={<SecurityEvents />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/policies" element={<Policies />} />
          <Route path="/simulator" element={<Simulator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
