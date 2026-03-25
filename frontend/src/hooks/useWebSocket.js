import { useEffect, useRef, useCallback } from 'react'
import useWorkflowStore from '../store/workflowStore'

const WS_BASE = 'ws://127.0.0.1:8000'

export function useWebSocket(meetingId = null) {
  const wsRef = useRef(null)
  const addLiveEvent = useWorkflowStore((s) => s.addLiveEvent)
  const updateMeetingStatus = useWorkflowStore((s) => s.updateMeetingStatus)

  const connect = useCallback(() => {
    const url = meetingId
      ? `${WS_BASE}/ws/workflow/${meetingId}`
      : `${WS_BASE}/ws/global`

    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`[WS] Connected: ${url}`)
    }

    ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data)
        addLiveEvent(event)

        // Update meeting status on workflow events
        if (event.event_type === 'workflow_complete' && event.meeting_id) {
          updateMeetingStatus(event.meeting_id, 'completed')
        }
      } catch (e) {
        console.warn('[WS] Parse error:', e)
      }
    }

    ws.onerror = (e) => {
      console.warn('[WS] Error:', e)
    }

    ws.onclose = () => {
      console.log('[WS] Disconnected — reconnecting in 3s...')
      setTimeout(connect, 3000)
    }
  }, [meetingId, addLiveEvent, updateMeetingStatus])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on unmount
        wsRef.current.close()
      }
    }
  }, [connect])

  return { ws: wsRef.current }
}

export default useWebSocket
