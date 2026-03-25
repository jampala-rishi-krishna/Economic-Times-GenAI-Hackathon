import React, { useState } from 'react'
import { Shield, CheckCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react'
import AgentBadge from '../shared/AgentBadge'
import { tamperAuditLog } from '../../api/client'
import toast from 'react-hot-toast'

export default function AuditEntry({ log, showTamper }) {
  const [expanded, setExpanded] = useState(false)
  const [checksum, setChecksum] = useState(log.checksum_valid)
  const [tampered, setTampered] = useState(false)

  const handleTamper = async (e) => {
    e.stopPropagation()
    try {
      await tamperAuditLog(log.id)
      setChecksum(false)
      setTampered(true)
      toast.error('⚠️ Integrity violation detected!', {
        style: { background: '#1a0000', color: '#EF4444', border: '1px solid #EF4444' }
      })
    } catch {
      toast.error('Tamper simulation failed')
    }
  }

  return (
    <div style={{
      borderLeft: `3px solid ${log.is_human_override ? '#F4C542' : '#2563EB'}`,
      paddingLeft: '16px',
      marginBottom: '16px',
      position: 'relative'
    }}>
      {/* Timeline dot */}
      <div style={{
        position: 'absolute', left: '-8px', top: '10px',
        width: '13px', height: '13px', borderRadius: '50%',
        background: log.is_human_override ? '#F4C542' : '#2563EB',
        border: '2px solid #FFFFFF'
      }} />

      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          background: '#F8FAFC',
          border: `1px solid ${tampered ? '#EF444466' : '#E2E8F0'}`,
          borderRadius: '10px',
          padding: '14px',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
      >
        {/* Top row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <AgentBadge agentName={log.actor} />
            {log.is_human_override && <span style={{ fontSize: '13px' }} title="Human override">🧑</span>}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            {/* Checksum status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {checksum && !tampered ? (
                <><CheckCircle size={13} color="#10B981" /><span style={{ fontSize: '10px', color: '#10B981', fontFamily: 'monospace' }}>VERIFIED</span></>
              ) : (
                <><XCircle size={13} color="#EF4444" /><span style={{ fontSize: '10px', color: '#EF4444', fontFamily: 'monospace' }}>TAMPERED</span></>
              )}
            </div>
            {showTamper && !tampered && (
              <button
                onClick={handleTamper}
                style={{
                  background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                  borderRadius: '5px', padding: '2px 7px', cursor: 'pointer',
                  color: '#EF4444', fontSize: '9px', fontWeight: '600'
                }}
              >
                TAMPER
              </button>
            )}
            <span style={{ fontSize: '9px', color: '#475569', fontFamily: 'monospace' }}>
              {new Date(log.timestamp).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Action */}
        <div style={{ fontSize: '13px', fontWeight: '600', color: '#0F172A', marginBottom: '6px' }}>
          {log.action}
        </div>

        {/* Target */}
        {log.target_type && (
          <div style={{ display: 'flex', gap: '6px', marginBottom: '6px', flexWrap: 'wrap' }}>
            <span style={{
              background: 'rgba(124,58,237,0.15)', color: '#A78BFA',
              fontSize: '10px', padding: '1px 7px', borderRadius: '4px', fontFamily: 'monospace'
            }}>{log.target_type}</span>
            {log.target_id && (
              <span style={{
                background: 'rgba(0,212,255,0.1)', color: '#2563EB',
                fontSize: '10px', padding: '1px 7px', borderRadius: '4px', fontFamily: 'monospace'
              }}>{log.target_id?.slice(0, 12)}...</span>
            )}
          </div>
        )}

        {/* Rationale */}
        {log.decision_rationale && (
          <div style={{
            fontSize: '12px', color: '#475569', fontStyle: 'italic',
            marginTop: '4px', lineHeight: '1.5'
          }}>
            "{log.decision_rationale?.slice(0, 150)}{log.decision_rationale?.length > 150 ? '...' : ''}"
          </div>
        )}

        {/* Checksum */}
        <div style={{
          marginTop: '10px', display: 'flex', alignItems: 'center', gap: '6px'
        }}>
          <Shield size={11} color={checksum && !tampered ? '#10B981' : '#EF4444'} />
          <span style={{ fontSize: '10px', fontFamily: 'monospace', color: '#475569' }}>
            SHA256: {log.checksum?.slice(0, 24)}...
          </span>
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#475569' }}
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        </div>

        {/* Expanded JSON */}
        {expanded && (log.before_state || log.after_state) && (
          <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {log.before_state && (
              <div>
                <div style={{ fontSize: '10px', color: '#EF4444', fontFamily: 'monospace', marginBottom: '4px' }}>BEFORE</div>
                <pre style={{
                  background: '#FFFFFF', borderRadius: '6px', padding: '8px',
                  fontSize: '10px', color: '#475569', overflow: 'auto', maxHeight: '80px',
                  fontFamily: 'monospace'
                }}>{JSON.stringify(log.before_state, null, 2)}</pre>
              </div>
            )}
            {log.after_state && (
              <div>
                <div style={{ fontSize: '10px', color: '#10B981', fontFamily: 'monospace', marginBottom: '4px' }}>AFTER</div>
                <pre style={{
                  background: '#FFFFFF', borderRadius: '6px', padding: '8px',
                  fontSize: '10px', color: '#475569', overflow: 'auto', maxHeight: '80px',
                  fontFamily: 'monospace'
                }}>{JSON.stringify(log.after_state, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
