import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Clusters from './pages/Clusters'
import ClusterDetail from './pages/ClusterDetail'
import Reservations from './pages/Reservations'
import Calendar from './pages/Calendar'
import Testing from './pages/Testing'
import Results from './pages/Results'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="clusters" element={<Clusters />} />
        <Route path="clusters/:id" element={<ClusterDetail />} />
        <Route path="reservations" element={<Reservations />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="testing" element={<Testing />} />
        <Route path="results" element={<Results />} />
      </Route>
    </Routes>
  )
}

export default App
