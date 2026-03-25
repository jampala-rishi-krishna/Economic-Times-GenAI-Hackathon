import React from 'react'
import { Users, CheckSquare, Brain, Trash2, Play } from 'lucide-react'
import StatusPill from '../shared/StatusPill'
import { useWorkflow } from '../../hooks/useWorkflow'
import { deleteMeeting } from '../../api/client'
import toast from 'react-hot-toast'

function Avatar({ name, color }) {
  return (
    <div title={name} style={{
      width: '26px', height: '26px', borderRadius: '50%',
      background: color || 'rgba(124,58,237,0.3)',
      border: '2px solid #F8FAFC',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '10px', fontWeight: '700', color: '#0F172A',
      marginLeft: '-6px'
    }}>
      {name?.[0]?.toUpperCase()}
    </div>
  )
}

const AVATAR_COLORS = ['rgba(0,212,255,0.4)', 'rgba(124,58,237,0.4)', 'rgba(16,185,129,0.4)', 'rgba(244,197,66,0.4)']

export default function MeetingCard({ meeting, onDelete, onSelect }) {
  const { launchWorkflow } = useWorkflow()
  const participants = meeting.participants || []

  const handleDelete = async (e) => {
    e.stopPropagation()
    try {
      await deleteMeeting(meeting.id)
      onDelete?.(meeting.id)
      toast.success('Meeting deleted')
    } catch {
      toast.error('Failed to delete meeting')
    }
  }

  const handleLaunch = async (e) => {
    e.stopPropagation()
    await launchWorkflow(meeting.id)
  }

  return (
    <div
      className="glass-card"
      onClick={() => onSelect?.(meeting)}
      style={{
        padding: '18px',
        cursor: 'pointer',
        position: 'relative',
        borderLeft: meeting.status === 'completed' ? '3px solid #10B981'
          : meeting.status === 'processing' ? '3px solid #2563EB'
          : meeting.status === 'failed' ? '3px solid #EF4444'
          : '3px solid #E2E8F0'
      }}
    >
      {/* Status + Actions */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px' }}>
        <StatusPill status={meeting.status} />
        <div style={{ display: 'flex', gap: '6px' }}>
          {meeting.status === 'pending' && (
            <button onClick={handleLaunch} title="Launch workflow" style={{
              background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.3)',
              borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', color: '#2563EB', fontSize: '12px'
            }}>
              <Play size={12} />
            </button>
          )}
          <button onClick={handleDelete} title="Delete" style={{
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', color: '#EF4444', fontSize: '12px'
          }}>
            <Trash2 size={12} />
          </button>
        </div>
      </div>

      {/* Title */}
      <div style={{
        fontSize: '14px', fontWeight: '700',
        color: '#0F172A', marginBottom: '6px',
        lineHeight: '1.3',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
      }}>{meeting.title}</div>

      {/* Date */}
      <div style={{ fontSize: '11px', color: '#475569', marginBottom: '12px', fontFamily: 'monospace' }}>
        {new Date(meeting.uploaded_at).toLocaleString()}
      </div>

      {/* Participants */}
      {participants.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', marginRight: '8px' }}>
            {participants.slice(0, 4).map((p, i) => (
              <Avatar key={p} name={p} color={AVATAR_COLORS[i % AVATAR_COLORS.length]} />
            ))}
          </div>
          <span style={{ fontSize: '11px', color: '#475569' }}>
            {participants.slice(0, 4).join(', ')}
            {participants.length > 4 && ` +${participants.length - 4}`}
          </span>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Brain size={11} color="#7C3AED" />
          <span style={{ fontSize: '11px', color: '#475569' }}>
            {meeting.decisions_count || 0} decisions
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CheckSquare size={11} color="#10B981" />
          <span style={{ fontSize: '11px', color: '#475569' }}>
            {meeting.tasks_count || 0} tasks
          </span>
        </div>
      </div>

      {/* Processing animation overlay */}
      {meeting.status === 'processing' && (
        <div className="processing-card" style={{
          position: 'absolute', inset: 0, borderRadius: '12px',
          pointerEvents: 'none'
        }} />
      )}
    </div>
  )
}
