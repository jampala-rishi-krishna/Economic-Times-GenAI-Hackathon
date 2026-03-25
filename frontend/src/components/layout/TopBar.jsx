import React, { useState } from 'react'
import { Search, Bell, Settings, UserCheck } from 'lucide-react'
import useWorkflowStore from '../../store/workflowStore'
import NotificationDrawer from './NotificationDrawer'
import toast from 'react-hot-toast'

export default function TopBar({ title }) {
  const { notifications } = useWorkflowStore()
  const [isNoteOpen, setIsNoteOpen] = useState(false)
  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <>
      <header style={{
        position: 'fixed', top: 0, left: '220px', right: 0, height: '64px',
        background: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '0 24px', zIndex: 100
      }}>
        {/* Title/Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '15px', fontWeight: '700', color: '#0F172A', fontFamily: 'monospace', letterSpacing: '1px' }}>
            {title}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* Search Mock */}
          <div className="hidden lg:flex" style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            background: '#F8FAFC', border: '1px solid #E2E8F0',
            borderRadius: '8px', padding: '6px 12px', minWidth: '300px'
          }}>
            <Search size={14} color="#475569" />
            <input
              type="text"
              placeholder="Search tasks, agents, audit logs..."
              style={{
                background: 'transparent', border: 'none', color: '#0F172A',
                fontSize: '12px', outline: 'none', width: '100%',
                fontFamily: 'sans-serif'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => toast.success('Human Override mode active', {
                icon: '🧑',
                style: { border: '1px solid #F4C542', color: '#F4C542', background: '#F8FAFC' }
              })}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: 'rgba(244,197,66,0.1)', border: '1px solid rgba(244,197,66,0.4)',
                borderRadius: '8px', padding: '6px 14px', color: '#F4C542',
                fontSize: '12px', fontWeight: '600', cursor: 'pointer'
              }}
            >
              <UserCheck size={14} />
              Override
            </button>

            <button 
              onClick={() => setIsNoteOpen(true)}
              style={{
                position: 'relative', background: 'rgba(124,58,237,0.1)', 
                border: '1px solid rgba(124,58,237,0.3)',
                borderRadius: '8px', padding: '8px', cursor: 'pointer', 
                color: '#A78BFA', display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}
            >
              <Bell size={18} />
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute', top: '-5px', right: '-5px',
                  minWidth: '18px', height: '18px', background: '#EF4444',
                  borderRadius: '10px', border: '2px solid #FFFFFF',
                  fontSize: '9px', color: 'white', fontWeight: '800',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  padding: '0 4px'
                }}>
                  {unreadCount}
                </span>
              )}
            </button>

            <button style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#475569' }}>
              <Settings size={18} />
            </button>
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'linear-gradient(45deg, #2563EB, #7C3AED)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '11px', fontWeight: '700', color: 'white',
              cursor: 'pointer', border: '2px solid #E2E8F0'
            }}>
              RK
            </div>
          </div>
        </div>
      </header>

      <NotificationDrawer 
        isOpen={isNoteOpen} 
        onClose={() => setIsNoteOpen(false)} 
      />
    </>
  )
}
