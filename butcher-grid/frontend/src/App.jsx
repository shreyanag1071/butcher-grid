import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './components/AuthContext'
import Login from './pages/Login'
import FarmDashboard from './pages/FarmDashboard'
import LogMedication from './pages/LogMedication'
import LogWaste from './pages/LogWaste'
import RegulatorDashboard from './pages/RegulatorDashboard'
import QRScan from './pages/QRScan'

function PrivateRoute({ children, role }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" />
  if (role && user.role !== role) return <Navigate to={user.role === 'regulator' ? '/regulator' : '/farm'} />
  return children
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" />
  return <Navigate to={user.role === 'regulator' ? '/regulator' : '/farm'} />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />
          <Route path="/scan" element={<QRScan />} />

          <Route path="/farm" element={<PrivateRoute><FarmDashboard /></PrivateRoute>} />
          <Route path="/farm/medication" element={<PrivateRoute><LogMedication /></PrivateRoute>} />
          <Route path="/farm/waste" element={<PrivateRoute><LogWaste /></PrivateRoute>} />

          <Route path="/regulator" element={<PrivateRoute role="regulator"><RegulatorDashboard /></PrivateRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
