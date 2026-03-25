import React, { useState } from 'react'
import { AlertTriangle, Clock, User, Flag, ChevronRight } from 'lucide-react'
import StatusPill from '../shared/StatusPill'

const PRIORITY_COLORS = {
  critical: '#EF4444',
  high: '#F59E0B',
  medium: '#2563EB',
  low: '#475569'
}

const PRIORITY_LABELS = {
  critical: '🔴 CRITICAL',
  high: '🟠 HIGH',
  medium: '🔵 MEDIUM',
  low: '⚪ LOW'
}

export default function TaskCard({ task, onClick }) {
  const isOverdue = task.due_date && new Date(task.due_date) < new Date()
  const priorityColor = PRIORITY_COLORS[task.priority] || '#475569'

  return (
    <div
      onClick={() => onClick?.(task)}
      style={{
        background: '#F8FAFC',
        border: `1px solid ${task.status === 'escalated' ? '#EF444466' : '#E2E8F0'}`,
        borderRadius: '10px',
        padding: '14px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        position: 'relative',
        borderLeft: `3px solid ${priorityColor}`,
        animation: task.status === 'escalated' ? 'pulse-border 2s infinite' : 'none'
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = `${priorityColor}88`
        e.currentTarget.style.transform = 'translateY(-1px)'
        e.currentTarget.style.boxShadow = `0 4px 12px ${priorityColor}22`
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = task.status === 'escalated' ? '#EF444466' : '#E2E8F0'
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      {/* Priority + Escalation count */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{
          fontSize: '9px', fontWeight: '700', color: priorityColor,
          fontFamily: 'monospace', letterSpacing: '0.05em'
        }}>
          {PRIORITY_LABELS[task.priority]}
        </span>
        {task.escalation_count > 0 && (
          <span style={{
            background: '#EF444422', border: '1px solid #EF444444',
            color: '#EF4444', borderRadius: '999px',
            fontSize: '9px', padding: '1px 6px', fontWeight: '700'
          }}>
            ⚡ {task.escalation_count}x escalated
          </span>
        )}
      </div>

      {/* Title */}
      <div style={{
        fontSize: '13px', fontWeight: '600', color: '#0F172A',
        lineHeight: '1.4', marginBottom: '10px',
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {task.title}
      </div>

      {/* Assignee */}
      {task.assigned_to && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '6px' }}>
          <div style={{
            width: '20px', height: '20px', borderRadius: '50%',
            background: 'rgba(124,58,237,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '9px', fontWeight: '700', color: '#A78BFA'
          }}>
            {task.assigned_to[0]?.toUpperCase()}
          </div>
          <span style={{ fontSize: '11px', color: '#475569' }}>{task.assigned_to}</span>
          {task.is_human_override && (
            <span title="Human override" style={{ fontSize: '11px' }}>🧑</span>
          )}
        </div>
      )}

      {/* Due date */}
      {task.due_date && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '4px',
          fontSize: '10px', color: isOverdue ? '#EF4444' : '#475569',
          fontFamily: 'monospace'
        }}>
          <Clock size={10} />
          {isOverdue ? '⚠ OVERDUE: ' : ''}
          {new Date(task.due_date).toLocaleDateString()}
        </div>
      )}

      {/* Stall timer */}
      {task.stall_detected_at && task.status === 'stalled' && (
        <div style={{
          marginTop: '6px', fontSize: '10px', color: '#F59E0B',
          display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'monospace'
        }}>
          <AlertTriangle size={10} />
          Stalled {Math.round((Date.now() - new Date(task.stall_detected_at)) / 3600000)}h ago
        </div>
      )}

      <ChevronRight size={14} color="#475569" style={{ position: 'absolute', bottom: '12px', right: '12px' }} />
    </div>
  )
}
