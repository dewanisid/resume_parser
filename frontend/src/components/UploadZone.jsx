/**
 * UploadZone — drag-and-drop + click-to-upload PDF input.
 *
 * This is a "controlled" component — it doesn't manage its own upload state.
 * It just handles the UI for picking a file, then calls onUpload(file) and
 * lets the parent (Dashboard) handle the actual API call and state updates.
 *
 * PROPS:
 *  - onUpload(file)  : called when the user selects or drops a valid PDF
 *  - isUploading     : boolean — disables the zone while an upload is in progress
 *
 * DRAG-AND-DROP EXPLAINED:
 * Browsers fire drag events: onDragOver, onDragLeave, onDrop.
 * - onDragOver: fires while a file is hovering — we call e.preventDefault() to
 *   tell the browser "I'll handle this drop, don't open the file yourself"
 * - onDrop: fires when the file is released — we extract it from e.dataTransfer.files
 * - We also use a hidden <input type="file"> triggered by a click for accessibility
 */

import { useRef, useState } from 'react'

export default function UploadZone({ onUpload, isUploading }) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)  // ref lets us programmatically click the hidden input

  function validateAndUpload(file) {
    setError('')
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10 MB
      setError('File must be smaller than 10 MB.')
      return
    }

    onUpload(file)
  }

  function handleDragOver(e) {
    e.preventDefault()  // required — without this, drop won't fire
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    validateAndUpload(file)
  }

  function handleInputChange(e) {
    const file = e.target.files[0]
    validateAndUpload(file)
    // Reset the input so the same file can be re-uploaded if needed
    e.target.value = ''
  }

  return (
    <div>
      {/* The drop zone — clicking it triggers the hidden file input */}
      <div
        onClick={() => !isUploading && inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={[
          'flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 cursor-pointer transition-colors',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/30',
          isUploading ? 'opacity-50 cursor-not-allowed' : '',
        ].join(' ')}
      >
        {/* Upload icon */}
        <div className="mb-3 text-4xl text-muted-foreground">
          {isUploading ? '⏳' : '📄'}
        </div>

        <p className="font-medium text-sm">
          {isUploading
            ? 'Uploading...'
            : isDragging
            ? 'Drop your PDF here'
            : 'Drag & drop a PDF, or click to browse'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          PDF only · Max 10 MB
        </p>
      </div>

      {/* Hidden file input — triggered programmatically by clicking the zone above */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleInputChange}
        disabled={isUploading}
      />

      {/* Client-side validation error */}
      {error && (
        <p className="mt-2 text-sm text-destructive">{error}</p>
      )}
    </div>
  )
}
