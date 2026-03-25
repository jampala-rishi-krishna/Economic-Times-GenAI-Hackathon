import { create } from 'zustand'

const useWorkflowStore = create((set, get) => ({
  // Live agent events from WebSocket
  liveEvents: [],
  // Active meeting workflows
  activeWorkflows: new Set(),
  // Dashboard stats
  stats: null,
  // Meetings list
  meetings: [],
  // Tasks
  tasks: [],
  // Audit logs
  auditLogs: [],
  // Notifications
  notifications: [],
  // WebSocket connections per meeting
  wsConnections: {},

  addLiveEvent: (event) =>
    set((state) => {
      const newState = {
        liveEvents: [event, ...state.liveEvents].slice(0, 200)
      };
      
      // If it's an escalation or a task assignment, add it to notifications
      if (['escalation', 'task_assigned', 'error'].includes(event.event_type)) {
        newState.notifications = [
          {
            id: event.event_id || Math.random().toString(36).substr(2, 9),
            type: event.event_type,
            message: event.message,
            timestamp: event.timestamp || new Date().toISOString(),
            read: false,
            agent: event.agent_name
          },
          ...state.notifications
        ].slice(0, 50);
      }
      
      return newState;
    }),

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map(n => n.id === id ? { ...n, read: true } : n)
    })),

  clearNotifications: () => set({ notifications: [] }),

  clearEvents: () => set({ liveEvents: [] }),

  setStats: (stats) => set({ stats }),
  setMeetings: (meetings) => set({ meetings }),
  setTasks: (tasks) => set({ tasks }),
  setAuditLogs: (auditLogs) => set({ auditLogs }),

  addMeeting: (meeting) =>
    set((state) => ({ meetings: [meeting, ...state.meetings] })),

  updateMeetingStatus: (id, status) =>
    set((state) => ({
      meetings: state.meetings.map((m) =>
        m.id === id ? { ...m, status } : m
      )
    })),

  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === id ? { ...t, ...updates } : t
      )
    })),

  setWorkflowActive: (meetingId, active) =>
    set((state) => {
      const ws = new Set(state.activeWorkflows)
      active ? ws.add(meetingId) : ws.delete(meetingId)
      return { activeWorkflows: ws }
    }),

  clearAllData: () => set({
    meetings: [],
    tasks: [],
    auditLogs: [],
    liveEvents: [],
    notifications: [],
    stats: {
      total_meetings: 0,
      total_tasks: 0,
      completed_tasks: 0,
      escalated_tasks: 0,
      autonomy_score: 0
    }
  })
}))

export default useWorkflowStore
