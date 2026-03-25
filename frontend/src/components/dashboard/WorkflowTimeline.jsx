import React from 'react'

const PHASES = [
  { key: 'ingest', label: 'Ingest', agent: 'Transcription Agent', icon: '📋' },
  { key: 'extract', label: 'Extract', agent: 'Decision Agent', icon: '🔍' },
  { key: 'create', label: 'Create Tasks', agent: 'Task Creator', icon: '📝' },
  { key: 'assign', label: 'Assign', agent: 'Assignor Agent', icon: '👤' },
  { key: 'monitor', label: 'Monitor', agent: 'Monitor Agent', icon: '📊' },
  { key: 'escalate', label: 'Escalate', agent: 'Escalation Agent', icon: '🚨' },
]

function getPhaseStatus(meeting, phaseIdx) {
  if (!meeting) return 'idle'
  if (meeting.status === 'completed') return 'done'
  if (meeting.status === 'failed') return phaseIdx === 0 ? 'error' : 'idle'
  if (meeting.status === 'processing') return phaseIdx === 0 ? 'active' : 'idle'
  return 'idle'
}

export default function WorkflowTimeline({ meetings = [] }) {
  const recentMeetings = meetings.slice(0, 4)

  return (
    <div style={{
      background: '#F8FAFC',
      border: '1px solid #E2E8F0',
      borderRadius: '12px',
      padding: '18px',
      height: '420px',
      overflowY: 'auto'
    }}>
      <div style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: '600', color: '#0F172A', marginBottom: '16px' }}>
        Workflow Timeline
      </div>

      {recentMeetings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#475569' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>📅</div>
          <div style={{ fontSize: '13px' }}>No meetings yet</div>
        </div>
      ) : (
        recentMeetings.map((meeting) => (
          <div key={meeting.id} style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', fontWeight: '600', color: '#0F172A', marginBottom: '8px', truncate: true }}>
              {meeting.title?.slice(0, 30)}...
            </div>
            {/* Phase dots */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {PHASES.map((phase, idx) => {
                const isDone = meeting.status === 'completed'
                const isActive = meeting.status === 'processing' && !isDone
                const color = isDone ? '#10B981' : isActive && idx === 0 ? '#2563EB' : '#E2E8F0'
                return (
                  <React.Fragment key={phase.key}>
                    <div
                      title={`${phase.label}: ${phase.agent}`}
                      style={{
                        width: '28px', height: '28px', borderRadius: '50%',
                        background: isDone ? 'rgba(16,185,129,0.2)' : isActive && idx === 0 ? 'rgba(0,212,255,0.2)' : '#0F172A',
                        border: `2px solid ${color}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '11px',
                        animation: isActive && idx === 0 ? 'breathe 1.5s ease-in-out infinite' : 'none'
                      }}
                    >
                      {isDone ? '✓' : phase.icon}
                    </div>
                    {idx < PHASES.length - 1 && (
                      <div style={{
                        flex: 1, height: '2px',
                        background: isDone ? '#10B981' : '#E2E8F0',
                        borderRadius: '1px'
                      }} />
                    )}
                  </React.Fragment>
                )
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
              <span style={{ fontSize: '9px', color: '#475569' }}>
                {new Date(meeting.uploaded_at).toLocaleDateString()}
              </span>
              <span style={{
                fontSize: '9px', fontWeight: '600',
                color: meeting.status === 'completed' ? '#10B981'
                  : meeting.status === 'processing' ? '#2563EB'
                  : '#475569'
              }}>{meeting.status?.toUpperCase()}</span>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
