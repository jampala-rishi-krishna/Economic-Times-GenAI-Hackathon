import React, { useState } from 'react'
import TaskCard from './TaskCard'
import TaskDetailModal from './TaskDetailModal'

const COLUMNS = [
  { id: 'created', label: 'Created', color: '#7C3AED', icon: '●' },
  { id: 'in_progress', label: 'In Progress', color: '#2563EB', icon: '▶' },
  { id: 'stalled', label: 'Stalled', color: '#F59E0B', icon: '⏸' },
  { id: 'escalated', label: 'Escalated', color: '#EF4444', icon: '🚨' },
  { id: 'completed', label: 'Completed', color: '#10B981', icon: '✓' },
]

export default function KanbanBoard({ tasks = [], onTaskUpdate }) {
  const [selectedTask, setSelectedTask] = useState(null)

  const getColumnTasks = (status) => tasks.filter(t => t.status === status)

  return (
    <>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '12px',
        alignItems: 'start'
      }}>
        {COLUMNS.map(col => {
          const colTasks = getColumnTasks(col.id)
          return (
            <div key={col.id} style={{
              background: '#F8FAFC',
              border: `1px solid ${col.id === 'escalated' ? '#EF444433' : '#E2E8F0'}`,
              borderTop: `2px solid ${col.color}`,
              borderRadius: '10px',
              padding: '12px',
              minHeight: '200px'
            }}>
              {/* Column Header */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                marginBottom: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: col.color, fontSize: '13px' }}>{col.icon}</span>
                  <span style={{
                    fontSize: '12px', fontWeight: '700', color: '#0F172A',
                    fontFamily: 'monospace'
                  }}>{col.label}</span>
                </div>
                <span style={{
                  background: `${col.color}22`, color: col.color,
                  borderRadius: '999px', fontSize: '10px', padding: '1px 8px',
                  fontWeight: '700', border: `1px solid ${col.color}44`
                }}>{colTasks.length}</span>
              </div>

              {/* Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {colTasks.length === 0 ? (
                  <div style={{
                    padding: '24px', textAlign: 'center',
                    color: '#475569', fontSize: '12px',
                    border: '1px dashed #E2E8F0', borderRadius: '8px'
                  }}>
                    No tasks
                  </div>
                ) : (
                  colTasks.map(task => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onClick={setSelectedTask}
                    />
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>

      {selectedTask && (
        <TaskDetailModal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdate={(updatedTask) => {
            onTaskUpdate?.(updatedTask)
            setSelectedTask(updatedTask)
          }}
        />
      )}
    </>
  )
}
