import React, { useEffect, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import KanbanBoard from '../components/tasks/KanbanBoard'
import useWorkflowStore from '../store/workflowStore'
import { getTasks, getMeetings } from '../api/client'
import useWebSocket from '../hooks/useWebSocket'

export default function Tasks() {
  const { tasks, setTasks, meetings, setMeetings, updateTask } = useWorkflowStore()
  const [loading, setLoading] = useState(true)
  const [filterMeeting, setFilterMeeting] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterAssignee, setFilterAssignee] = useState('')
  useWebSocket()

  useEffect(() => {
    Promise.all([getTasks(), getMeetings()]).then(([t, m]) => {
      setTasks(t)
      setMeetings(m)
      setLoading(false)
    }).catch(() => setLoading(false))

    const interval = setInterval(() => {
      getTasks().then(t => setTasks(t)).catch(() => {})
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const filteredTasks = tasks.filter(t => {
    if (filterMeeting && t.meeting_id !== filterMeeting) return false
    if (filterPriority && t.priority !== filterPriority) return false
    if (filterAssignee && !t.assigned_to?.toLowerCase().includes(filterAssignee.toLowerCase())) return false
    return true
  })

  const allAssignees = [...new Set(tasks.map(t => t.assigned_to).filter(Boolean))]

  return (
    <div>
      <TopBar title="NEXUS // Task Board" />
      <div style={{ paddingTop: '84px', padding: '80px 24px 24px' }}>

        {/* Filter bar */}
        <div style={{
          display: 'flex', gap: '10px', marginBottom: '20px',
          background: '#F8FAFC', border: '1px solid #E2E8F0',
          borderRadius: '10px', padding: '12px 16px', alignItems: 'center'
        }}>
          <select
            value={filterMeeting}
            onChange={e => setFilterMeeting(e.target.value)}
            style={{
              background: '#0F172A', border: '1px solid #E2E8F0', color: '#475569',
              borderRadius: '7px', padding: '6px 10px', fontSize: '12px', outline: 'none',
              fontFamily: 'sans-serif'
            }}
          >
            <option value="">All Meetings</option>
            {meetings.map(m => <option key={m.id} value={m.id}>{m.title?.slice(0, 30)}</option>)}
          </select>

          <select
            value={filterPriority}
            onChange={e => setFilterPriority(e.target.value)}
            style={{
              background: '#0F172A', border: '1px solid #E2E8F0', color: '#475569',
              borderRadius: '7px', padding: '6px 10px', fontSize: '12px', outline: 'none',
              fontFamily: 'sans-serif'
            }}
          >
            <option value="">All Priorities</option>
            {['critical', 'high', 'medium', 'low'].map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
          </select>

          <input
            value={filterAssignee}
            onChange={e => setFilterAssignee(e.target.value)}
            placeholder="Filter by assignee..."
            style={{
              background: '#0F172A', border: '1px solid #E2E8F0', color: '#475569',
              borderRadius: '7px', padding: '6px 10px', fontSize: '12px', outline: 'none',
              fontFamily: 'sans-serif', minWidth: '160px'
            }}
          />

          <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#475569' }}>
            {filteredTasks.length} tasks
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '80px', color: '#475569' }}>Loading tasks...</div>
        ) : (
          <KanbanBoard
            tasks={filteredTasks}
            onTaskUpdate={(updated) => updateTask(updated.id, updated)}
          />
        )}
      </div>
    </div>
  )
}
