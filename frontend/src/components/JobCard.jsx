/**
 * JobCard — displays one resume parse job in the history list.
 *
 * PROPS:
 *  - job       : the job object from the API
 *  - onDelete  : called with jobId when the user clicks Delete
 *
 * STATUS COLOURS:
 * We use shadcn's Badge component with different variants:
 *  pending     → outline  (neutral, empty border)
 *  processing  → secondary (muted blue/grey)
 *  completed   → default  (dark/primary — stands out positively)
 *  failed      → destructive (red)
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

// Maps job status → shadcn Badge variant
function statusVariant(status) {
  switch (status) {
    case 'completed':  return 'default'
    case 'processing': return 'secondary'
    case 'pending':    return 'outline'
    case 'failed':     return 'destructive'
    default:           return 'outline'
  }
}

// Formats a file size in bytes to a human-readable string (e.g. "2.4 MB")
function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Formats an ISO date string to a short readable date (e.g. "Mar 6, 2026")
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

export default function JobCard({ job, onDelete }) {
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!confirm(`Delete "${job.original_filename}"? This cannot be undone.`)) return
    setDeleting(true)
    await onDelete(job.id)
    // Note: we don't setDeleting(false) because the card will be removed from the list
  }

  const isActive = job.status === 'pending' || job.status === 'processing'

  return (
    <div className="flex items-center justify-between rounded-lg border p-4 bg-card">
      {/* Left side: filename, size, date, status */}
      <div className="flex flex-col gap-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate max-w-xs">
            {job.original_filename}
          </span>
          <Badge variant={statusVariant(job.status)}>
            {/* Show animated dot for active jobs */}
            {isActive && (
              <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
            )}
            {job.status}
          </Badge>
        </div>

        <span className="text-xs text-muted-foreground">
          {formatSize(job.file_size_bytes)} · {formatDate(job.created_at)}
        </span>

        {/* Show error message if parsing failed */}
        {job.status === 'failed' && job.error_message && (
          <p className="text-xs text-destructive mt-1 max-w-sm truncate" title={job.error_message}>
            {job.error_message}
          </p>
        )}
      </div>

      {/* Right side: action buttons */}
      <div className="flex items-center gap-2 ml-4 shrink-0">
        {/* View Results button — only shown when parsing completed */}
        {job.status === 'completed' && job.result?.data_id && (
          <Button asChild size="sm">
            <Link to={`/results/${job.result.data_id}`}>View Results</Link>
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          disabled={deleting}
          className="text-muted-foreground hover:text-destructive"
        >
          {deleting ? '...' : 'Delete'}
        </Button>
      </div>
    </div>
  )
}
