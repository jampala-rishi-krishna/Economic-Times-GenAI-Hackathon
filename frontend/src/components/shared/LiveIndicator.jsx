import React from 'react'

export default function LiveIndicator({ label = 'LIVE' }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '6px',
      padding: '3px 10px',
      background: 'rgba(0,212,255,0.1)',
      border: '1px solid rgba(0,212,255,0.3)',
      borderRadius: '999px',
      fontSize: '10px', fontWeight: '700',
      color: '#2563EB', fontFamily: 'monospace',
      letterSpacing: '0.1em'
    }}>
      <span className="live-dot" />
      {label}
    </span>
  )
}
