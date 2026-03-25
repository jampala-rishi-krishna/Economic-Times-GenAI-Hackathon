import React, { useEffect, useState } from 'react'
import TopBar from '../components/layout/TopBar'
import AuditEntry from '../components/audit/AuditEntry'
import { getAuditLogs, getMeetings } from '../api/client'
import { Shield, Download, AlertTriangle } from 'lucide-react'

export default function AuditTrail() {
  const [logs, setLogs] = useState([])
  const [meetings, setMeetings] = useState([])
  const [filterMeeting, setFilterMeeting] = useState('')
  const [loading, setLoading] = useState(true)
  const [showTamper, setShowTamper] = useState(false)

  useEffect(() => {
    Promise.all([getAuditLogs(), getMeetings()]).then(([l, m]) => {
      setLogs(l)
      setMeetings(m)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const filteredLogs = filterMeeting ? logs.filter(l => l.meeting_id === filterMeeting) : logs

  const downloadLogs = () => {
    const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'nexus-audit-trail.json'
    a.click()
  }

  const tamperedCount = filteredLogs.filter(l => !l.checksum_valid).length
  const verifiedCount = filteredLogs.filter(l => l.checksum_valid).length

  return (
    <div>
      <TopBar title="NEXUS // Audit Trail" />
      <div style={{ paddingTop: '84px', padding: '80px 24px 24px', maxWidth: '900px', margin: '0 auto' }}>

        {/* Header card */}
        <div style={{
          background: '#F8FAFC', border: '1px solid #E2E8F0',
          borderRadius: '12px', padding: '20px',
          marginBottom: '20px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={24} color="#2563EB" />
            <div>
              <div style={{ fontFamily: 'monospace', fontSize: '15px', fontWeight: '700', color: '#0F172A' }}>
                Immutable Decision Audit Trail
              </div>
              <div style={{ fontSize: '12px', color: '#475569', marginTop: '2px' }}>
                {verifiedCount} entries verified ·
                {tamperedCount > 0 ? <span style={{ color: '#EF4444' }}> {tamperedCount} tampered</span> : <span style={{ color: '#10B981' }}> 0 tampered</span>}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={() => setShowTamper(!showTamper)}
              style={{
                background: showTamper ? 'rgba(239,68,68,0.2)' : 'rgba(239,68,68,0.08)',
                border: `1px solid rgba(239,68,68,${showTamper ? '0.6' : '0.3'})`,
                borderRadius: '7px', padding: '7px 12px',
                color: '#EF4444', fontSize: '11px', cursor: 'pointer', fontWeight: '600',
                display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'sans-serif'
              }}
            >
              <AlertTriangle size={12} />
              {showTamper ? 'Hide' : 'Show'} Tamper Sim
            </button>
            <button
              onClick={downloadLogs}
              style={{
                background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.3)',
                borderRadius: '7px', padding: '7px 12px',
                color: '#2563EB', fontSize: '11px', cursor: 'pointer', fontWeight: '600',
                display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'sans-serif'
              }}
            >
              <Download size={12} /> Export JSON
            </button>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <select
            value={filterMeeting}
            onChange={e => setFilterMeeting(e.target.value)}
            style={{
              background: '#F8FAFC', border: '1px solid #E2E8F0', color: '#475569',
              borderRadius: '7px', padding: '6px 12px', fontSize: '12px', outline: 'none', fontFamily: 'sans-serif'
            }}
          >
            <option value="">All Meetings</option>
            {meetings.map(m => <option key={m.id} value={m.id}>{m.title?.slice(0, 35)}</option>)}
          </select>
          <div style={{ fontSize: '12px', color: '#475569', display: 'flex', alignItems: 'center' }}>
            {filteredLogs.length} audit entries
          </div>
        </div>

        {/* Timeline */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '80px', color: '#475569' }}>Loading audit trail...</div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px', color: '#475569' }}>
            <Shield size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <div>No audit entries yet</div>
          </div>
        ) : (
          <div style={{ paddingLeft: '20px' }}>
            {filteredLogs.map(log => (
              <AuditEntry key={log.id} log={log} showTamper={showTamper} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
