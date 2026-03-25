import React, { useEffect, useRef, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import useWorkflowStore from '../store/workflowStore'
import useWebSocket from '../hooks/useWebSocket'
import LiveIndicator from '../components/shared/LiveIndicator'
import { Pause, Play } from 'lucide-react'

const AGENTS = [
  { name: 'Transcription Agent', role: 'Senior Meeting Analyst', icon: '📋', color: '#2563EB' },
  { name: 'Decision Extraction Agent', role: 'Decision Intelligence Specialist', icon: '🔍', color: '#7C3AED' },
  { name: 'Task Creator Agent', role: 'Project Management Architect', icon: '📝', color: '#10B981' },
  { name: 'Assignor Agent', role: 'Resource & Ownership Specialist', icon: '👤', color: '#F4C542' },
  { name: 'Progress Monitor Agent', role: 'Workflow Health Monitor', icon: '📊', color: '#F59E0B' },
  { name: 'Escalation Agent', role: 'Autonomous Escalation Manager', icon: '🚨', color: '#EF4444' },
]

const EVENT_COLORS = {
  agent_started: '#2563EB',
  agent_thinking: '#475569',
  tool_call: '#F4C542',
  decision_made: '#10B981',
  task_created: '#7C3AED',
  task_assigned: '#A78BFA',
  escalation: '#EF4444',
  workflow_complete: '#F4C542',
  workflow_started: '#2563EB',
  error: '#EF4444',
}

export default function AgentMonitor() {
  const liveEvents = useWorkflowStore(s => s.liveEvents)
  const [paused, setPaused] = useState(false)
  const [displayEvents, setDisplayEvents] = useState([])
  const terminalRef = useRef(null)
  useWebSocket()

  useEffect(() => {
    if (!paused) {
      setDisplayEvents(liveEvents.slice(0, 50))
      if (terminalRef.current) {
        terminalRef.current.scrollTop = 0
      }
    }
  }, [liveEvents, paused])

  // Get stats per agent
  const getAgentStats = (agentName) => {
    const agentEvents = liveEvents.filter(e => e.agent_name === agentName)
    const lastEvent = agentEvents[0]
    return {
      events: agentEvents.length,
      isActive: lastEvent && Date.now() - new Date(lastEvent.timestamp) < 10000,
      lastEventType: lastEvent?.event_type || 'idle',
      lastMessage: lastEvent?.message?.slice(0, 50) || 'Idle'
    }
  }

  return (
    <div>
      <TopBar title="NEXUS // Agent Monitor" />
      <div style={{ paddingTop: '84px', padding: '80px 24px 24px' }}>

        {/* Agent Hex Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px',
          marginBottom: '24px'
        }}>
          {AGENTS.map(agent => {
            const stats = getAgentStats(agent.name)
            return (
              <div key={agent.name} style={{
                background: '#F8FAFC',
                border: `1px solid ${stats.isActive ? agent.color + '88' : '#E2E8F0'}`,
                borderTop: `2px solid ${agent.color}`,
                borderRadius: '12px',
                padding: '16px 12px',
                textAlign: 'center',
                transition: 'all 0.3s ease',
                boxShadow: stats.isActive ? `0 0 16px ${agent.color}33` : 'none'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>{agent.icon}</div>
                <div style={{
                  fontSize: '11px', fontWeight: '700', color: agent.color,
                  fontFamily: 'monospace', marginBottom: '4px'
                }}>
                  {agent.name.replace(' Agent', '').replace(' Extraction', '\nExtraction')}
                </div>
                <div style={{ fontSize: '9px', color: '#475569', marginBottom: '10px' }}>
                  {agent.role}
                </div>

                {/* Status */}
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '4px',
                  padding: '2px 8px', borderRadius: '999px',
                  background: stats.isActive ? `${agent.color}22` : 'rgba(71,85,105,0.2)',
                  border: `1px solid ${stats.isActive ? agent.color + '44' : '#374151'}`,
                  fontSize: '9px', color: stats.isActive ? agent.color : '#475569',
                  fontWeight: '600', fontFamily: 'monospace'
                }}>
                  {stats.isActive ? (
                    <><span style={{ width: '5px', height: '5px', borderRadius: '50%', background: agent.color, animation: 'breathe 1s ease-in-out infinite', display: 'inline-block' }} />ACTIVE</>
                  ) : 'IDLE'}
                </div>

                <div style={{ fontSize: '10px', color: '#475569', marginTop: '8px' }}>
                  {stats.events} events
                </div>
              </div>
            )
          })}
        </div>

        {/* Live Console */}
        <div style={{
          background: '#F8FAFC', border: '1px solid #E2E8F0',
          borderRadius: '12px', overflow: 'hidden'
        }}>
          <div style={{
            padding: '12px 16px', borderBottom: '1px solid #E2E8F0',
            display: 'flex', alignItems: 'center', gap: '12px',
            background: '#FFFFFF'
          }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#EF4444' }} />
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#F59E0B' }} />
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10B981' }} />
            </div>
            <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#475569' }}>
              nexus-agent-console — Live Event Stream
            </span>
            <LiveIndicator />
            <button
              onClick={() => setPaused(!paused)}
              style={{
                marginLeft: 'auto',
                background: paused ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                border: `1px solid ${paused ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
                borderRadius: '6px', padding: '4px 10px',
                color: paused ? '#10B981' : '#F59E0B',
                fontSize: '11px', cursor: 'pointer', fontFamily: 'sans-serif',
                display: 'flex', alignItems: 'center', gap: '5px'
              }}
            >
              {paused ? <><Play size={12} /> Resume</> : <><Pause size={12} /> Pause</>}
            </button>
          </div>

          <div ref={terminalRef} className="terminal" style={{ height: '380px', overflowY: 'auto' }}>
            {displayEvents.length === 0 ? (
              <div style={{ color: '#475569', textAlign: 'center', paddingTop: '60px' }}>
                Waiting for events... Upload a meeting to start a workflow.
              </div>
            ) : (
              displayEvents.map((evt, i) => (
                <div key={evt.event_id} style={{
                  marginBottom: '6px',
                  color: EVENT_COLORS[evt.event_type] || '#475569',
                  animation: i === 0 && !paused ? 'slideInRight 0.2s ease-out' : 'none'
                }}>
                  <span style={{ color: '#475569' }}>
                    [{new Date(evt.timestamp).toLocaleTimeString()}]
                  </span>
                  {' '}
                  <span style={{ color: EVENT_COLORS[evt.event_type] || '#475569', fontWeight: '600' }}>
                    [{evt.event_type?.toUpperCase()}]
                  </span>
                  {' '}
                  <span style={{ color: '#F1F5F9' }}>{evt.agent_name}</span>
                  {' → '}
                  <span style={{ color: '#CBD5E1' }}>{evt.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
