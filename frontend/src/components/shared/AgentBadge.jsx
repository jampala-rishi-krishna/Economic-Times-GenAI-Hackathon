import React from 'react'

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

const AGENT_ICONS = {
  'Transcription Agent': '📋',
  'Decision Extraction Agent': '🔍',
  'Task Creator Agent': '📝',
  'Assignor Agent': '👤',
  'Progress Monitor Agent': '📊',
  'Escalation Agent': '🚨',
  'NEXUS Orchestrator': '⚡',
}

export default function AgentBadge({ agentName, isActive = false, size = 'sm' }) {
  const color = AGENT_COLORS[agentName] || AGENT_COLORS.default
  const icon = AGENT_ICONS[agentName] || '🤖'

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: size === 'sm' ? '2px 8px' : '4px 12px',
      borderRadius: '6px',
      background: `${color}18`,
      border: `1px solid ${color}44`,
      fontSize: size === 'sm' ? '11px' : '13px',
      fontWeight: '600',
      color: color,
      whiteSpace: 'nowrap'
    }}>
      <span style={{ fontSize: '10px' }}>{icon}</span>
      {agentName}
      {isActive && (
        <span style={{
          width: '6px', height: '6px', borderRadius: '50%',
          background: color, animation: 'breathe 1.5s ease-in-out infinite',
          marginLeft: '2px'
        }} />
      )}
    </span>
  )
}
