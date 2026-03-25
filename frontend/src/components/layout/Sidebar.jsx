import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Video, CheckSquare, Shield, Activity, Zap } from 'lucide-react'
import useWorkflowStore from '../../store/workflowStore'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/meetings', icon: Video, label: 'Meetings' },
  { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { path: '/audit', icon: Shield, label: 'Audit Trail' },
  { path: '/agents', icon: Activity, label: 'Agent Monitor' },
]

export default function Sidebar() {
  const tasks = useWorkflowStore(s => s.tasks)
  const escalatedCount = tasks.filter(t => t.status === 'escalated').length

  return (
    <aside style={{
      width: '220px',
      minHeight: '100vh',
      background: '#FFFFFF',
      borderRight: '1px solid #E2E8F0',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      position: 'fixed',
      top: 0, left: 0, bottom: 0,
      zIndex: 100
    }}>
      {/* Logo */}
      <div style={{ marginBottom: '32px', paddingLeft: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px',
            background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
            borderRadius: '8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap size={18} color="white" />
          </div>
          <div>
            <div style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: '16px', fontWeight: '700',
              background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '0.1em'
            }}>NEXUS</div>
            <div style={{ fontSize: '9px', color: '#475569', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              Enterprise AI
            </div>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={18} />
            <span style={{ fontSize: '14px', fontWeight: '500' }}>{label}</span>
            {label === 'Tasks' && escalatedCount > 0 && (
              <span style={{
                marginLeft: 'auto',
                background: '#EF4444',
                color: 'white',
                borderRadius: '999px',
                fontSize: '10px',
                padding: '1px 7px',
                fontWeight: '700'
              }}>{escalatedCount}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px',
        background: 'rgba(0,212,255,0.05)',
        borderRadius: '10px',
        border: '1px solid rgba(0,212,255,0.1)',
        marginTop: '16px'
      }}>
        <div style={{ fontSize: '10px', color: '#475569', fontFamily: 'monospace', marginBottom: '4px' }}>
          ET Hackathon 2025
        </div>
        <div style={{ fontSize: '11px', color: '#2563EB' }}>
          ● System Online
        </div>
      </div>
    </aside>
  )
}
