import React, { useState, useRef } from 'react'
import { Upload, FileText, Users, Play, Mail, ChevronDown, ChevronRight } from 'lucide-react'
import { saveParticipantEmails } from '../../api/client'
import toast from 'react-hot-toast'
import { useWorkflow } from '../../hooks/useWorkflow'

const SAMPLE_TRANSCRIPT = `Sarah (CPO): Alright team, let's confirm what we decided last week regarding the API migration.
James, you're taking ownership of the v2 API documentation, right? We need that done by end of next Friday.

James (Engineering Lead): Yes confirmed. I'll have the full API docs and migration guide ready by October 18th.

Sarah: Great. Priya, we agreed that QA needs to set up the automated testing suite for the new endpoints.
Can we get that done in two weeks?

Priya (QA Lead): Absolutely. I'll set up the test suite and have initial coverage report by October 25th.

Sarah: Perfect. Marcus, the product spec for the customer portal redesign — we decided to delay
that to next quarter, but you need to prepare a scope document by this Friday so we can budget properly.

Marcus (PM): Got it. Scope doc for customer portal redesign by Friday October 13th.

Sarah: Also, I'm assigning myself to finalize the Q4 OKRs document and share it with
the board by Wednesday. That's critical priority.

James: One more thing — we decided to retire the legacy webhook system.
I'll need DevOps support. Can someone flag that for the infrastructure team?

Sarah: Yes, Marcus — can you own that? Get a deprecation plan from the infra team by October 20th.

Marcus: Will do.`

export default function MeetingUploader({ onMeetingCreated }) {
  const [title, setTitle] = useState('')
  const [transcript, setTranscript] = useState('')
  const [participants, setParticipants] = useState('Sarah, James, Priya, Marcus')
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef()
  const [emailMap, setEmailMap] = useState({})
  const [showEmails, setShowEmails] = useState(false)
  const { uploadAndLaunch } = useWorkflow()

  // Derived list of participant names
  const partNames = participants.split(',').map(p => p.trim()).filter(Boolean)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type === 'text/plain') {
      const reader = new FileReader()
      reader.onload = (evt) => setTranscript(evt.target.result)
      reader.readAsText(file)
    } else {
      toast.error('Please drop a .txt file')
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (evt) => setTranscript(evt.target.result)
      reader.readAsText(file)
    }
  }

  const handleLaunch = async () => {
    if (!title.trim()) { toast.error('Please enter a meeting title'); return }
    if (!transcript.trim()) { toast.error('Please provide a transcript'); return }
    setLoading(true)
    try {
      const parts = participants.split(',').map(p => p.trim()).filter(Boolean)
      const meeting = await uploadAndLaunch(title, transcript, parts)
      
      // Save emails if any
      const mappings = Object.entries(emailMap)
        .filter(([_, email]) => email.trim())
        .map(([name, email]) => ({ participant_name: name, email_address: email }))
      
      if (mappings.length > 0) {
        await saveParticipantEmails(meeting.id, mappings)
        toast.success(`📧 Linked ${mappings.length} emails`)
      }

      onMeetingCreated?.(meeting)
      setTitle('')
      setTranscript('')
      setEmailMap({})
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      background: '#F8FAFC',
      border: '1px solid #E2E8F0',
      borderRadius: '12px',
      padding: '24px',
      marginBottom: '24px'
    }}>
      <div style={{
        fontFamily: 'monospace', fontSize: '13px', fontWeight: '600',
        color: '#0F172A', marginBottom: '20px',
        display: 'flex', alignItems: 'center', gap: '8px'
      }}>
        <Upload size={16} color="#2563EB" />
        Upload Meeting Transcript
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        {/* Title */}
        <div>
          <label style={{ fontSize: '11px', color: '#475569', fontFamily: 'monospace', display: 'block', marginBottom: '6px' }}>
            MEETING TITLE *
          </label>
          <input
            className="nexus-input"
            placeholder="e.g. Q4 Product Strategy Meeting"
            value={title}
            onChange={e => setTitle(e.target.value)}
          />
        </div>
        {/* Participants */}
        <div>
          <label style={{ fontSize: '11px', color: '#475569', fontFamily: 'monospace', display: 'block', marginBottom: '6px' }}>
            PARTICIPANTS (comma-separated)
          </label>
          <div style={{ position: 'relative' }}>
            <Users size={14} color="#475569" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              className="nexus-input"
              style={{ paddingLeft: '32px' }}
              placeholder="Sarah, James, Priya..."
              value={participants}
              onChange={e => setParticipants(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? '#2563EB' : '#E2E8F0'}`,
          borderRadius: '10px',
          padding: '16px',
          marginBottom: '12px',
          transition: 'all 0.2s',
          background: dragOver ? 'rgba(0,212,255,0.05)' : 'transparent'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
          <FileText size={14} color="#475569" style={{ marginTop: '2px', flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <textarea
              className="nexus-input"
              placeholder="Paste meeting transcript here or drag & drop a .txt file..."
              value={transcript}
              onChange={e => setTranscript(e.target.value)}
              rows={8}
              style={{ resize: 'vertical', minHeight: '120px' }}
            />
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <button
            onClick={() => fileRef.current?.click()}
            style={{
              background: 'rgba(124,58,237,0.1)',
              border: '1px solid rgba(124,58,237,0.3)',
              borderRadius: '6px', padding: '5px 12px',
              color: '#A78BFA', fontSize: '11px', cursor: 'pointer', fontFamily: 'sans-serif'
            }}
          >
            📁 Browse File
          </button>
          <button
            onClick={() => { setTranscript(SAMPLE_TRANSCRIPT); setTitle('Q4 Product Strategy Meeting') }}
            style={{
              background: 'rgba(0,212,255,0.1)',
              border: '1px solid rgba(0,212,255,0.3)',
              borderRadius: '6px', padding: '5px 12px',
              color: '#2563EB', fontSize: '11px', cursor: 'pointer', fontFamily: 'sans-serif'
            }}
          >
            ⚡ Load Sample
          </button>
          <input ref={fileRef} type="file" accept=".txt" style={{ display: 'none' }} onChange={handleFileSelect} />
        </div>
      </div>

      {/* Email Mapping Section */}
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={() => setShowEmails(!showEmails)}
          style={{
            background: 'transparent', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '8px',
            color: '#475569', fontSize: '12px', fontFamily: 'monospace',
            padding: '4px 0', opacity: partNames.length > 0 ? 1 : 0.5
          }}
        >
          {showEmails ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Mail size={14} color="#2563EB" />
          MAP PARTICIPANT EMAILS ({partNames.length})
        </button>

        {showEmails && partNames.length > 0 && (
          <div style={{
            marginTop: '12px', background: 'rgba(0,212,255,0.02)', 
            border: '1px solid #E2E8F0', borderRadius: '8px', 
            padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
            gap: '12px'
          }}>
            {partNames.map(name => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ 
                  flex: '0 0 100px', fontSize: '11px', color: '#0F172A', 
                  fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' 
                }}>
                  {name}
                </div>
                <input 
                  className="nexus-input"
                  style={{ height: '32px', fontSize: '11px' }}
                  placeholder="name@email.com"
                  value={emailMap[name] || ''}
                  onChange={e => setEmailMap({ ...emailMap, [name]: e.target.value })}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleLaunch}
        disabled={loading}
        className="btn-primary"
        style={{
          width: '100%', padding: '12px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
          fontSize: '14px', opacity: loading ? 0.7 : 1,
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        <Play size={16} />
        {loading ? 'Launching Workflow...' : '🚀 Launch NEXUS Workflow'}
      </button>
    </div>
  )
}
