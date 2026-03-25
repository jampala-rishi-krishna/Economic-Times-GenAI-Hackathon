import React, { useEffect, useState } from 'react'
import { getDashboardStats } from '../../api/client'
import useWorkflowStore from '../../store/workflowStore'

function AnimatedNumber({ value, suffix = '' }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    const start = 0
    const end = parseFloat(value) || 0
    const duration = 800
    const step = (end - start) / (duration / 16)
    let current = start
    const timer = setInterval(() => {
      current += step
      if (current >= end) { setDisplay(end); clearInterval(timer) }
      else setDisplay(Math.floor(current))
    }, 16)
    return () => clearInterval(timer)
  }, [value])
  return <span>{typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(1) : display}{suffix}</span>
}

export default function StatsGrid({ stats }) {
  const cards = [
    {
      label: 'Meetings Processed',
      value: stats?.total_meetings || 0,
      suffix: '',
      color: 'cyan',
      icon: '🎯',
      sub: 'Total analyzed'
    },
    {
      label: 'Tasks Created',
      value: stats?.total_tasks || 0,
      suffix: '',
      color: 'violet',
      icon: '📋',
      sub: `${stats?.completed_tasks || 0} completed`
    },
    {
      label: 'Autonomy Score',
      value: stats?.autonomy_score || 0,
      suffix: '%',
      color: 'success',
      icon: '🤖',
      sub: 'Zero human involvement'
    },
    {
      label: 'Active Escalations',
      value: stats?.escalated_tasks || 0,
      suffix: '',
      color: stats?.escalated_tasks > 0 ? 'danger' : 'success',
      icon: stats?.escalated_tasks > 0 ? '🚨' : '✅',
      sub: stats?.escalated_tasks > 0 ? 'Requires attention' : 'All clear'
    },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
      {cards.map((card, i) => (
        <div key={i} className={`stat-card ${card.color}`} style={{ animation: `fadeUp 0.4s ease-out ${i * 0.1}s both` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div style={{ fontSize: '22px' }}>{card.icon}</div>
            <div style={{
              padding: '3px 8px', borderRadius: '6px',
              background: 'rgba(255,255,255,0.05)',
              fontSize: '10px', color: '#475569', fontFamily: 'monospace'
            }}>LIVE</div>
          </div>
          <div style={{
            fontSize: '36px', fontWeight: '700',
            fontFamily: "'Space Mono', monospace",
            color: card.color === 'cyan' ? '#2563EB'
              : card.color === 'violet' ? '#A78BFA'
              : card.color === 'success' ? '#10B981'
              : '#EF4444',
            letterSpacing: '-0.02em', lineHeight: 1
          }}>
            <AnimatedNumber value={card.value} suffix={card.suffix} />
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', fontWeight: '600', color: '#0F172A' }}>
            {card.label}
          </div>
          <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>
            {card.sub}
          </div>
        </div>
      ))}
    </div>
  )
}
