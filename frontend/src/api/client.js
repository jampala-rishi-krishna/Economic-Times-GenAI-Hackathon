import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
})

// Meetings
export const getMeetings = () => api.get('/api/meetings').then(r => r.data)
export const getMeeting = (id) => api.get(`/api/meetings/${id}`).then(r => r.data)
export const deleteMeeting = (id) =>
  api.delete(`/api/meetings/${id}`).then(r => r.data)

export const getMeetingNotifications = (id) =>
  api.get(`/api/meetings/${id}/notifications`).then(r => r.data)
export const createMeeting = (formData) =>
  api.post('/api/meetings', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data)

export const saveParticipantEmails = (meetingId, participants) =>
  api.post('/api/meetings/participants/emails', { meeting_id: meetingId, participants }).then(r => r.data)

// Workflow
export const startWorkflow = (meetingId) =>
  api.post(`/api/workflow/start/${meetingId}`).then(r => r.data)
export const getWorkflowStatus = (meetingId) =>
  api.get(`/api/workflow/status/${meetingId}`).then(r => r.data)
export const getAgentEvents = (meetingId) =>
  api.get(`/api/workflow/agents/events/${meetingId}`).then(r => r.data)

// Tasks
export const getTasks = (params = {}) =>
  api.get('/api/tasks', { params }).then(r => r.data)
export const updateTask = (id, data) =>
  api.put(`/api/tasks/${id}`, data).then(r => r.data)
export const completeTask = (id) =>
  api.post(`/api/tasks/${id}/complete`).then(r => r.data)
export const escalateTask = (id) =>
  api.post(`/api/tasks/${id}/escalate`).then(r => r.data)

// Audit
export const getAuditLogs = (meetingId) =>
  api.get(meetingId ? `/api/audit/${meetingId}` : '/api/audit').then(r => r.data)
export const verifyAuditLog = (logId) =>
  api.get(`/api/audit/verify/${logId}`).then(r => r.data)
export const tamperAuditLog = (logId) =>
  api.post(`/api/audit/tamper/${logId}`).then(r => r.data)

// Dashboard
export const getDashboardStats = () =>
  api.get('/api/dashboard/stats').then(r => r.data)

// System
export const clearSystemData = () =>
  api.post('/api/system/clear').then(r => r.data)

export default api
