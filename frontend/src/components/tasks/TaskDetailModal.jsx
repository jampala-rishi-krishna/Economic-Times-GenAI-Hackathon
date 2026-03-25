import React, { useState } from 'react'
import { X, CheckCircle, AlertTriangle, UserCheck } from 'lucide-react'
import { completeTask, escalateTask, updateTask } from '../../api/client'
import toast from 'react-hot-toast'
import StatusPill from '../shared/StatusPill'

export default function TaskDetailModal({ task, onClose, onUpdate }) {
  const [loading, setLoading] = useState(false)

  const handleComplete = async () => {
    setLoading(true)
    try {
      await completeTask(task.id)
      onUpdate?.({ ...task, status: 'completed', is_human_override: true })
      toast.success('✅ Task marked complete')
    } catch { toast.error('Failed') }
    finally { setLoading(false) }
  }

  const handleEscalate = async () => {
    setLoading(true)
    try {
      await escalateTask(task.id)
      onUpdate?.({ ...task, status: 'escalated', escalation_count: (task.escalation_count || 0) + 1, is_human_override: true })
      toast.success('🚨 Task escalated')
    } catch { toast.error('Failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div style={{ padding: '24px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
            <div>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <StatusPill status={task.status} />
                <span className={`pill priority-${task.priority}`}>{task.priority?.toUpperCase()}</span>
                {task.is_human_override && (
                  <span style={{ fontSize: '11px', color: '#F4C542' }}>🧑 Human Override</span>
                )}
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#0F172A', lineHeight: '1.3' }}>
                {task.title}
              </h2>
            </div>
            <button onClick={onClose} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              color: '#475569', padding: '4px'
            }}>
              <X size={20} />
            </button>
          </div>

          {/* Description */}
          {task.description && (
            <div style={{ marginBottom: '20px' }}>
              <div className="section-header">DESCRIPTION</div>
              <p style={{ fontSize: '13px', color: '#475569', lineHeight: '1.6' }}>
                {task.description}
              </p>
            </div>
          )}

          {/* Context Quote */}
          {task.context_quote && (
            <div style={{ marginBottom: '20px' }}>
              <div className="section-header">📍 SOURCE QUOTE FROM MEETING</div>
              <blockquote style={{
                borderLeft: '3px solid #2563EB',
                paddingLeft: '12px',
                fontSize: '12px',
                color: '#475569',
                fontStyle: 'italic',
                background: 'rgba(0,212,255,0.05)',
                borderRadius: '0 8px 8px 0',
                padding: '10px 12px'
              }}>
                {task.context_quote}
              </blockquote>
            </div>
          )}

          {/* Assignment Rationale */}
          {task.assignment_rationale && (
            <div style={{ marginBottom: '20px' }}>
              <div className="section-header">🤖 AI ASSIGNMENT RATIONALE</div>
              <p style={{
                fontSize: '12px', color: '#475569', lineHeight: '1.6',
                background: 'rgba(124,58,237,0.05)',
                border: '1px solid rgba(124,58,237,0.2)',
                borderRadius: '8px', padding: '10px 12px'
              }}>
                {task.assignment_rationale}
              </p>
            </div>
          )}

          {/* Details grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
            {[
              { label: 'Assigned To', value: task.assigned_to || 'Unassigned' },
              { label: 'Assigned By', value: task.assigned_by || '-' },
              { label: 'Due Date', value: task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No deadline' },
              { label: 'Escalations', value: task.escalation_count ? `${task.escalation_count}x` : 'None' },
            ].map(item => (
              <div key={item.label} style={{
                background: '#0F172A', borderRadius: '8px', padding: '10px 12px'
              }}>
                <div style={{ fontSize: '10px', color: '#475569', fontFamily: 'monospace', marginBottom: '4px' }}>
                  {item.label.toUpperCase()}
                </div>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#0F172A' }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '10px' }}>
            {task.status !== 'completed' && (
              <button
                onClick={handleComplete}
                disabled={loading}
                style={{
                  flex: 1, padding: '10px',
                  background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.4)',
                  borderRadius: '8px', color: '#10B981', fontSize: '13px',
                  fontWeight: '600', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                }}
              >
                <CheckCircle size={15} /> Mark Complete
              </button>
            )}
            {task.status !== 'escalated' && task.status !== 'completed' && (
              <button
                onClick={handleEscalate}
                disabled={loading}
                style={{
                  flex: 1, padding: '10px',
                  background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)',
                  borderRadius: '8px', color: '#EF4444', fontSize: '13px',
                  fontWeight: '600', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                }}
              >
                <AlertTriangle size={15} /> Escalate
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
