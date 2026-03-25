import { useCallback } from 'react'
import toast from 'react-hot-toast'
import { startWorkflow, createMeeting } from '../api/client'
import useWorkflowStore from '../store/workflowStore'

export function useWorkflow() {
  const store = useWorkflowStore()

  const launchWorkflow = useCallback(async (meetingId) => {
    try {
      store.setWorkflowActive(meetingId, true)
      store.updateMeetingStatus(meetingId, 'processing')
      await startWorkflow(meetingId)
      toast.success('🚀 Workflow started! Watch the live feed.', {
        style: { background: '#0D1421', color: '#00D4FF', border: '1px solid #1E293B' }
      })
    } catch (e) {
      store.setWorkflowActive(meetingId, false)
      toast.error('Failed to start workflow: ' + (e.response?.data?.detail || e.message))
    }
  }, [store])

  const uploadAndLaunch = useCallback(async (title, transcript, participants) => {
    try {
      const formData = new FormData()
      formData.append('title', title)
      formData.append('raw_transcript', transcript)
      formData.append('participants', JSON.stringify(participants))
      formData.append('duration_minutes', '45')

      const meeting = await createMeeting(formData)
      store.addMeeting(meeting)
      toast.success('Meeting uploaded!', {
        style: { background: '#0D1421', color: '#10B981', border: '1px solid #1E293B' }
      })

      await launchWorkflow(meeting.id)
      return meeting
    } catch (e) {
      toast.error('Upload failed: ' + (e.response?.data?.detail || e.message))
      throw e
    }
  }, [store, launchWorkflow])

  return { launchWorkflow, uploadAndLaunch }
}

export default useWorkflow
