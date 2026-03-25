import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Meetings from './pages/Meetings'
import Tasks from './pages/Tasks'
import AuditTrail from './pages/AuditTrail'
import AgentMonitor from './pages/AgentMonitor'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#F8FAFC', color: '#0F172A', border: '1px solid #E2E8F0' },
          duration: 4000
        }}
      />
      <div style={{ display: 'flex', minHeight: '100vh', background: '#FFFFFF' }}>
        <Sidebar />
        <main style={{ flex: 1, marginLeft: '220px', minHeight: '100vh', overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/meetings" element={<Meetings />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/audit" element={<AuditTrail />} />
            <Route path="/agents" element={<AgentMonitor />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
