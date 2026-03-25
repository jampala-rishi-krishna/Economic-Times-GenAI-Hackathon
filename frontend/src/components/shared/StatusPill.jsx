import React from 'react'

const STATUS_CONFIG = {
  pending: { label: 'Pending', cls: 'pill-pending', icon: '○' },
  processing: { label: 'Processing', cls: 'pill-processing', icon: '◈' },
  completed: { label: 'Completed', cls: 'pill-completed', icon: '✓' },
  failed: { label: 'Failed', cls: 'pill-failed', icon: '✗' },
  partial_completion: { label: 'Partial', cls: 'pill-stalled', icon: '⚡' },
  created: { label: 'Created', cls: 'pill-created', icon: '●' },
  in_progress: { label: 'In Progress', cls: 'pill-in_progress', icon: '▶' },
  stalled: { label: 'Stalled', cls: 'pill-stalled', icon: '⏸' },
  escalated: { label: 'Escalated', cls: 'pill-escalated', icon: '🚨' },
  cancelled: { label: 'Cancelled', cls: 'pill-pending', icon: '✗' },
}

export default function StatusPill({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span className={`pill ${cfg.cls}`}>
      <span>{cfg.icon}</span>
      {cfg.label}
    </span>
  )
}
