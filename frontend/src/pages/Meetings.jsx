import React, { useEffect, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import MeetingUploader from '../components/meetings/MeetingUploader'
import MeetingCard from '../components/meetings/MeetingCard'
import useWorkflowStore from '../store/workflowStore'
import { X, Mail, CheckCircle2, AlertCircle } from 'lucide-react'
import { getMeetings, getMeeting, getMeetingNotifications } from '../api/client'
import useWebSocket from '../hooks/useWebSocket'

export default function Meetings() {
  const { meetings, setMeetings, addMeeting } = useWorkflowStore()
  const [loading, setLoading] = useState(true)
  const [selectedMeeting, setSelectedMeeting] = useState(null)
  const [detail, setDetail] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [activeTab, setActiveTab] = useState('summary')
  useWebSocket()

  useEffect(() => {
    getMeetings().then(m => {
      setMeetings(m)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleSelect = async (meeting) => {
    setSelectedMeeting(meeting)
    setActiveTab('summary')
    try {
      const d = await getMeeting(meeting.id)
      setDetail(d)
      const n = await getMeetingNotifications(meeting.id)
      setNotifications(n)
    } catch {}
  }

  const handleDelete = (id) => {
    setMeetings(meetings.filter(m => m.id !== id))
    if (selectedMeeting?.id === id) { setSelectedMeeting(null); setDetail(null) }
  }

  return (
    <div>
      <TopBar title="NEXUS // Meetings" />
      <div style={{ paddingTop: '84px', padding: '80px 24px 24px' }}>

        <MeetingUploader onMeetingCreated={addMeeting} />

        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#475569', marginBottom: '12px' }}>
            {meetings.length} MEETINGS TOTAL
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px', color: '#475569' }}>Loading...</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              {meetings.map(m => (
                <MeetingCard
                  key={m.id}
                  meeting={m}
                  onDelete={handleDelete}
                  onSelect={handleSelect}
                />
              ))}
            </div>
          )}
        </div>

        {/* Meeting Detail Slide-over */}
        {selectedMeeting && (
          <div style={{
            position: 'fixed', top: 0, right: 0, bottom: 0, width: '500px',
            background: '#FFFFFF', borderLeft: '1px solid #E2E8F0',
            zIndex: 200, overflowY: 'auto',
            boxShadow: '-8px 0 40px rgba(0,0,0,0.1)',
            animation: 'slideInRight 0.3s ease-out'
          }}>
            {/* Close */}
            <div style={{ padding: '20px', borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontFamily: 'monospace', fontSize: '14px', fontWeight: '600', color: '#2563EB' }}>
                Meeting Detail
              </div>
              <button onClick={() => { setSelectedMeeting(null); setDetail(null) }}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#475569' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '20px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#0F172A', marginBottom: '8px' }}>
                {selectedMeeting.title}
              </h2>

              {/* Tabs simulation */}
              {detail ? (
                <>
                  {/* Tabs Logic */}
                  <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #E2E8F0', marginBottom: '20px' }}>
                    {['summary', 'decisions', 'tasks', 'notifications'].map(tab => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        style={{
                          padding: '8px 12px', background: 'transparent',
                          border: 'none', cursor: 'pointer', fontSize: '11px',
                          fontFamily: 'monospace', fontWeight: 'bold',
                          color: activeTab === tab ? '#2563EB' : '#475569',
                          borderBottom: activeTab === tab ? '2px solid #2563EB' : 'none',
                          marginBottom: '-1px'
                        }}
                      >
                        {tab.toUpperCase()}
                      </button>
                    ))}
                  </div>

                  {/* Summary */}
                  {activeTab === 'summary' && detail.meeting?.summary && (
                    <div style={{ marginBottom: '20px' }}>
                      <div className="section-header">AI SUMMARY</div>
                      <p style={{ fontSize: '12px', color: '#475569', lineHeight: '1.6', background: 'rgba(0,212,255,0.04)', borderRadius: '8px', padding: '10px' }}>
                        {detail.meeting.summary}
                      </p>
                    </div>
                  )}

                  {/* Decisions */}
                  {activeTab === 'decisions' && (
                    <div style={{ marginBottom: '20px' }}>
                      <div className="section-header">DECISIONS ({detail.decisions.length})</div>
                      {detail.decisions.length === 0 ? (
                         <div style={{ color: '#475569', fontSize: '12px', textAlign: 'center', padding: '20px' }}>No decisions extracted</div>
                      ) : detail.decisions.map((d, i) => (
                        <div key={d.id} style={{
                          background: '#F1F5F9', borderRadius: '8px', padding: '10px 12px',
                          marginBottom: '8px', borderLeft: '2px solid #7C3AED'
                        }}>
                          <div style={{ fontSize: '12px', color: '#0F172A', marginBottom: '4px' }}>{d.decision_text}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tasks */}
                  {activeTab === 'tasks' && (
                    <div>
                      <div className="section-header">TASKS ({detail.tasks.length})</div>
                      {detail.tasks.length === 0 ? (
                         <div style={{ color: '#475569', fontSize: '12px', textAlign: 'center', padding: '20px' }}>No tasks created</div>
                      ) : detail.tasks.map(t => (
                        <div key={t.id} style={{
                          background: '#F1F5F9', borderRadius: '8px', padding: '10px 12px',
                          marginBottom: '8px', borderLeft: '2px solid #2563EB'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ fontSize: '12px', color: '#0F172A' }}>{t.title}</div>
                            <span className={`pill priority-${t.priority}`}>{t.priority}</span>
                          </div>
                          <div style={{ fontSize: '10px', color: '#475569', marginTop: '4px' }}>→ {t.assigned_to || 'Unassigned'}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Notifications */}
                  {activeTab === 'notifications' && (
                    <div>
                      <div className="section-header">EMAIL DELIVERY STATUS</div>
                      {notifications.length === 0 ? (
                        <div style={{ color: '#475569', fontSize: '12px', textAlign: 'center', padding: '20px' }}>No notifications sent yet</div>
                      ) : notifications.map(n => (
                        <div key={n.id} style={{
                          background: n.email_sent ? 'rgba(16, 185, 129, 0.03)' : 'rgba(239, 68, 68, 0.03)',
                          borderRadius: '8px', padding: '12px',
                          marginBottom: '10px', border: n.email_sent ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#0F172A', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Mail size={12} />
                                {n.notification_type.toUpperCase()}
                              </div>
                              <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>To: {n.recipient}</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              {n.email_sent ? (
                                <div style={{ color: '#10B981', fontSize: '10px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <CheckCircle2 size={12} /> SENT
                                </div>
                              ) : (
                                <div style={{ color: '#EF4444', fontSize: '10px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <AlertCircle size={12} /> FAILED
                                </div>
                              )}
                              <div style={{ fontSize: '9px', color: '#475569', marginTop: '4px' }}>{new Date(n.sent_at).toLocaleTimeString()}</div>
                            </div>
                          </div>
                          {n.email_error && (
                            <div style={{ 
                              marginTop: '8px', padding: '6px', background: 'rgba(239, 68, 68, 0.1)', 
                              borderRadius: '4px', fontSize: '10px', color: '#EF4444', border: '1px solid rgba(239, 68, 68, 0.2)' 
                            }}>
                              ERROR: {n.email_error}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#475569' }}>Loading...</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
