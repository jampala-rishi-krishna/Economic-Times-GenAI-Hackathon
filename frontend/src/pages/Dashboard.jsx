import React, { useEffect, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import StatsGrid from '../components/dashboard/StatsGrid'
import AgentActivityFeed from '../components/dashboard/AgentActivityFeed'
import WorkflowTimeline from '../components/dashboard/WorkflowTimeline'
import useWorkflowStore from '../store/workflowStore'
import useWebSocket from '../hooks/useWebSocket'
import { getDashboardStats, getMeetings, getTasks, clearSystemData } from '../api/client'
import { Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const { setStats, setMeetings, setTasks, clearAllData, stats, meetings, tasks } = useWorkflowStore()
  const [loading, setLoading] = useState(true)
  const [isClearing, setIsClearing] = useState(false)
  useWebSocket() // global WebSocket

  const handleClearAll = async () => {
    if (!window.confirm("ARE YOU SURE? This will permanently delete all meetings, tasks, and audit logs. This cannot be undone.")) return;
    
    setIsClearing(true);
    const loadId = toast.loading("Clearing system database...");
    try {
      await clearSystemData();
      clearAllData();
      toast.success("System data purged successfully", { id: loadId });
    } catch (e) {
      toast.error("Failed to clear data: " + (e.response?.data?.detail || e.message), { id: loadId });
    } finally {
      setIsClearing(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [s, m, t] = await Promise.all([
          getDashboardStats(), getMeetings(), getTasks()
        ])
        setStats(s)
        setMeetings(m)
        setTasks(t)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
    const interval = setInterval(async () => {
      try {
        const [s, t] = await Promise.all([getDashboardStats(), getTasks()])
        setStats(s)
        setTasks(t)
      } catch {}
    }, 8000)
    return () => clearInterval(interval)
  }, [])

  // Task health breakdown per meeting
  const tasksByMeeting = meetings.slice(0, 4).map(m => {
    const mTasks = tasks.filter(t => t.meeting_id === m.id)
    return {
      meeting: m,
      created: mTasks.filter(t => t.status === 'created').length,
      in_progress: mTasks.filter(t => t.status === 'in_progress').length,
      stalled: mTasks.filter(t => t.status === 'stalled').length,
      escalated: mTasks.filter(t => t.status === 'escalated').length,
      completed: mTasks.filter(t => t.status === 'completed').length,
      total: mTasks.length
    }
  })

  return (
    <div>
      <TopBar title="NEXUS // Command Center" />
      <div style={{ paddingTop: '60px', padding: '80px 24px 24px', maxWidth: '1600px' }}>
        
        {/* Header with Clear Action */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#0F172A', fontFamily: 'monospace' }}>OPERATIONAL OVERVIEW</h2>
            <p style={{ fontSize: '12px', color: '#475569', marginTop: '4px' }}>Real-time autonomous intelligence monitoring</p>
          </div>
          <button
            onClick={handleClearAll}
            disabled={isClearing}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '8px', padding: '10px 16px', color: '#EF4444',
              fontSize: '11px', fontWeight: '700', cursor: 'pointer', fontFamily: 'monospace',
              transition: 'all 0.2s ease', opacity: isClearing ? 0.5 : 1
            }}
          >
            <Trash2 size={14} />
            PURGE SYSTEM DATA
          </button>
        </div>

        {/* Stats */}
        <StatsGrid stats={stats || {}} />

        {/* Live Feed + Timeline */}
        <div style={{ display: 'grid', gridTemplateColumns: '60% 40%', gap: '16px', marginTop: '16px' }}>
          <AgentActivityFeed />
          <WorkflowTimeline meetings={meetings} />
        </div>

        {/* Task Health + Autonomy */}
        <div style={{ display: 'grid', gridTemplateColumns: '55% 45%', gap: '16px', marginTop: '16px' }}>
          <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '12px', padding: '18px' }}>
            <div style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: '600', color: '#0F172A', marginBottom: '16px' }}>
              Task Health Overview
            </div>
            {tasksByMeeting.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px', color: '#475569', fontSize: '13px' }}>No meeting data yet</div>
            ) : tasksByMeeting.map(({ meeting, created, in_progress, stalled, escalated, completed, total }) => (
              <div key={meeting.id} style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#475569', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {meeting.title}
                </div>
                {total > 0 && (
                  <div style={{ display: 'flex', height: '14px', borderRadius: '7px', overflow: 'hidden', gap: '1px' }}>
                    {[
                      { count: completed, color: '#10B981' },
                      { count: in_progress, color: '#2563EB' },
                      { count: created, color: '#7C3AED' },
                      { count: stalled, color: '#F59E0B' },
                      { count: escalated, color: '#EF4444' },
                    ].filter(s => s.count > 0).map((seg, i) => (
                      <div key={i} style={{ flex: seg.count, background: seg.color, minWidth: '4px', opacity: 0.85 }} title={`${seg.count}`} />
                    ))}
                  </div>
                )}
                <div style={{ fontSize: '10px', color: '#475569', marginTop: '3px', display: 'flex', gap: '8px' }}>
                  {completed > 0 && <span style={{ color: '#10B981' }}>✓{completed}</span>}
                  {in_progress > 0 && <span style={{ color: '#2563EB' }}>▶{in_progress}</span>}
                  {stalled > 0 && <span style={{ color: '#F59E0B' }}>⏸{stalled}</span>}
                  {escalated > 0 && <span style={{ color: '#EF4444' }}>🚨{escalated}</span>}
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '12px', padding: '18px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: '600', color: '#0F172A', marginBottom: '24px', alignSelf: 'flex-start' }}>
              Autonomy Score
            </div>
            <div style={{ position: 'relative', width: '160px', height: '160px' }}>
              <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="80" cy="80" r="64" fill="none" stroke="#E2E8F0" strokeWidth="12" />
                <circle
                  cx="80" cy="80" r="64" fill="none"
                  stroke={stats?.autonomy_score > 80 ? '#10B981' : stats?.autonomy_score > 50 ? '#F59E0B' : '#EF4444'}
                  strokeWidth="12"
                  strokeDasharray={`${(stats?.autonomy_score || 0) / 100 * 402} 402`}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dasharray 1s ease' }}
                />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ fontSize: '36px', fontWeight: '700', fontFamily: "'Space Mono', monospace", color: stats?.autonomy_score > 80 ? '#10B981' : '#0F172A' }}>
                  {stats?.autonomy_score || 0}%
                </div>
                <div style={{ fontSize: '10px', color: '#475569', fontFamily: 'monospace' }}>AUTONOMOUS</div>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#475569', marginTop: '16px', textAlign: 'center' }}>
              {stats?.completed_tasks || 0} of {stats?.total_tasks || 0} tasks completed<br/>
              <span style={{ color: '#10B981' }}>without human intervention</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
