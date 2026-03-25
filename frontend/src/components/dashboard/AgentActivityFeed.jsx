import React, { useRef, useEffect } from 'react'
import useWorkflowStore from '../../store/workflowStore'
import AgentBadge from '../shared/AgentBadge'
import LiveIndicator from '../shared/LiveIndicator'

const AGENT_COLORS = {
  'Transcription Agent': '#2563EB',
  'Decision Extraction Agent': '#7C3AED',
  'Task Creator Agent': '#10B981',
  'Assignor Agent': '#F4C542',
  'Progress Monitor Agent': '#F59E0B',
  'Escalation Agent': '#EF4444',
  'NEXUS Orchestrator': '#475569',
  default: '#475569'
}

const EVENT_ICONS = {
  agent_started: '▶',
  agent_thinking: '💭',
  tool_call: '🔧',
  decision_made: '✓',
  task_created: '📋',
  task_assigned: '👤',
  escalation: '🚨',
  workflow_complete: '🎉',
  workflow_started: '🚀',
  error: '✗',
}

export default function AgentActivityFeed() {
  const liveEvents = useWorkflowStore(s => s.liveEvents)
  const feedRef = useRef(null)

  return (
    <div style={{
      background: '#F8FAFC',
      border: '1px solid #E2E8F0',
      borderRadius: '12px',
      display: 'flex', flexDirection: 'column',
      height: '420px'
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 18px',
        borderBottom: '1px solid #E2E8F0',
        display: 'flex', alignItems: 'center', gap: '10px'
      }}>
        <span style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: '600', color: '#0F172A' }}>
          Agent Activity Feed
        </span>
        <LiveIndicator />
        <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#475569' }}>
          {liveEvents.length} events
        </span>
      </div>

      {/* Feed */}
      <div ref={feedRef} style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {liveEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0', color: '#475569' }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>🤖</div>
            <div style={{ fontSize: '13px' }}>Waiting for agent activity...</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Upload a meeting to start</div>
          </div>
        ) : (
          liveEvents.map((event, i) => {
            const color = AGENT_COLORS[event.agent_name] || AGENT_COLORS.default
            const icon = EVENT_ICONS[event.event_type] || '•'
            const isNew = i === 0
            return (
              <div key={event.event_id} style={{
                display: 'flex', gap: '10px', marginBottom: '8px',
                padding: '10px',
                background: isNew ? `${color}08` : 'transparent',
                borderRadius: '8px',
                borderLeft: `2px solid ${color}`,
                animation: isNew ? 'slideInRight 0.3s ease-out' : 'none',
                transition: 'background 0.5s ease'
              }}>
                {/* Icon */}
                <div style={{
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: `${color}20`, border: `1px solid ${color}44`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '12px', flexShrink: 0, color: color
                }}>
                  {icon}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color }}>{event.agent_name}</span>
                    <span style={{
                      fontSize: '9px', color: '#475569', fontFamily: 'monospace',
                      background: '#0F172A', padding: '1px 5px', borderRadius: '4px'
                    }}>{event.event_type}</span>
                    <span style={{ marginLeft: 'auto', fontSize: '9px', color: '#475569', fontFamily: 'monospace', flexShrink: 0 }}>
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{
                    fontSize: '12px', color: '#475569', lineHeight: '1.4',
                    overflow: 'hidden', textOverflow: 'ellipsis',
                    display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical'
                  }}>
                    {event.message}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
