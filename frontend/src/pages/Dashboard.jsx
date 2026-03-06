/**
 * Dashboard — the main page after login.
 *
 * WHAT THIS PAGE DOES:
 *  1. On load: fetches the user's job history from the API
 *  2. Resumes polling for any jobs that are still pending/processing
 *  3. Provides an upload zone to parse a new resume
 *  4. Displays the job list, updating in real-time as jobs complete
 *
 * KEY CONCEPTS:
 *
 * useState: each piece of state that can change (jobs list, upload status, etc.)
 * useEffect: runs side effects (API calls, timers) after renders
 * useRef: holds mutable values that DON'T trigger re-renders when changed
 *         (perfect for interval IDs — we need them for cleanup but don't
 *          want every interval tick to re-render the component)
 *
 * POLLING EXPLAINED:
 * After uploading, we don't know when parsing finishes — it depends on Celery
 * and the Anthropic API. So we check the job status every 3 seconds until it
 * reaches "completed" or "failed". This is called polling.
 * A cleaner alternative would be WebSockets, but polling is simpler to understand.
 */

import { useState, useEffect, useRef } from 'react'
import { resumeApi } from '../api/client'
import UploadZone from '../components/UploadZone'
import JobCard from '../components/JobCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const POLL_INTERVAL_MS = 3000

export default function Dashboard() {
  const [jobs, setJobs] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [isLoadingJobs, setIsLoadingJobs] = useState(true)

  // pollingJobIds is a Set of job IDs we're currently watching
  // We use useState so the polling useEffect re-runs when it changes
  const [pollingJobIds, setPollingJobIds] = useState(new Set())

  // intervalsRef maps { jobId: intervalId }
  // We use useRef (not useState) because changing it shouldn't trigger a re-render
  const intervalsRef = useRef({})

  // ---------------------------------------------------------------------------
  // Load job history on mount
  // ---------------------------------------------------------------------------
  useEffect(() => {
    resumeApi.listJobs(1)
      .then(({ count, results }) => {
        setJobs(results)
        setTotalCount(count)

        // Automatically start polling for any jobs that are still in progress
        const activeIds = results
          .filter((j) => j.status === 'pending' || j.status === 'processing')
          .map((j) => j.id)

        if (activeIds.length > 0) {
          setPollingJobIds(new Set(activeIds))
        }
      })
      .catch(() => {
        // Silently fail — user will see an empty list
      })
      .finally(() => setIsLoadingJobs(false))
  }, []) // [] = run once on mount

  // ---------------------------------------------------------------------------
  // Polling — set up intervals for active jobs
  // ---------------------------------------------------------------------------
  useEffect(() => {
    // For each ID in pollingJobIds, set up an interval if one isn't running already
    pollingJobIds.forEach((jobId) => {
      if (intervalsRef.current[jobId]) return // already polling this one

      intervalsRef.current[jobId] = setInterval(async () => {
        try {
          const updatedJob = await resumeApi.getJob(jobId)

          // Replace the matching job in state with the fresh data
          setJobs((prev) =>
            prev.map((j) => (j.id === jobId ? updatedJob : j))
          )

          // Stop polling when the job reaches a terminal state
          if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            clearInterval(intervalsRef.current[jobId])
            delete intervalsRef.current[jobId]
            setPollingJobIds((prev) => {
              const next = new Set(prev)
              next.delete(jobId)
              return next
            })
          }
        } catch {
          // Swallow polling errors — the next tick will retry
        }
      }, POLL_INTERVAL_MS)
    })

    // Cleanup: clear all intervals when the component unmounts
    // This prevents the interval from trying to update state on an unmounted component
    return () => {
      Object.values(intervalsRef.current).forEach(clearInterval)
    }
  }, [pollingJobIds])

  // ---------------------------------------------------------------------------
  // Upload handler
  // ---------------------------------------------------------------------------
  async function handleUpload(file) {
    setIsUploading(true)
    setUploadError('')

    try {
      const { job_id, status } = await resumeApi.upload(file)

      // Optimistic update: add a placeholder job to the top of the list immediately
      // so the user sees feedback right away, before the server responds
      const optimisticJob = {
        id: job_id,
        status,
        original_filename: file.name,
        file_size_bytes: file.size,
        created_at: new Date().toISOString(),
        result: null,
      }
      setJobs((prev) => [optimisticJob, ...prev])
      setTotalCount((n) => n + 1)

      // Start polling the new job
      setPollingJobIds((prev) => new Set([...prev, job_id]))
    } catch (err) {
      setUploadError(err.response?.data?.error || 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Delete handler
  // ---------------------------------------------------------------------------
  async function handleDelete(jobId) {
    try {
      await resumeApi.deleteJob(jobId)

      // Remove from the list
      setJobs((prev) => prev.filter((j) => j.id !== jobId))
      setTotalCount((n) => Math.max(n - 1, 0))

      // Stop polling if we were watching this job
      if (intervalsRef.current[jobId]) {
        clearInterval(intervalsRef.current[jobId])
        delete intervalsRef.current[jobId]
      }
      setPollingJobIds((prev) => {
        const next = new Set(prev)
        next.delete(jobId)
        return next
      })
    } catch {
      // Could show a toast here in the future
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <main className="mx-auto max-w-3xl px-4 py-8 space-y-8">

      {/* Upload card */}
      <Card>
        <CardHeader>
          <CardTitle>Parse a Resume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <UploadZone onUpload={handleUpload} isUploading={isUploading} />
          {uploadError && (
            <p className="text-sm text-destructive">{uploadError}</p>
          )}
        </CardContent>
      </Card>

      {/* Job history */}
      <div>
        <h2 className="text-lg font-semibold mb-3">
          Your Resumes
          {totalCount > 0 && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({totalCount})
            </span>
          )}
        </h2>

        {isLoadingJobs ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No resumes yet. Upload one above to get started.
          </p>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
