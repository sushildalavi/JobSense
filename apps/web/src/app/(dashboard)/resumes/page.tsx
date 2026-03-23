'use client'

import { useState } from 'react'
import { Upload, FileUser } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getResumesApi } from '@/api/resumes'
import { QUERY_KEYS } from '@/lib/constants'
import { ResumeCard } from '@/components/resumes/resume-card'
import { ResumeUpload } from '@/components/resumes/resume-upload'
import { PageHeader } from '@/components/common/page-header'
import { EmptyState } from '@/components/common/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

export default function ResumesPage() {
  const [showUpload, setShowUpload] = useState(false)
  const { data: resumes, isLoading } = useQuery({
    queryKey: [QUERY_KEYS.RESUMES],
    queryFn: getResumesApi,
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resumes"
        badge={<Badge variant="muted" className="text-xs">{resumes?.length || 0} resumes</Badge>}
        subtitle="Manage your master resumes and tailored versions"
        action={
          <Button onClick={() => setShowUpload(true)} size="sm">
            <Upload className="w-4 h-4 mr-2" />
            Upload Resume
          </Button>
        }
      />

      {/* Upload modal */}
      <Dialog open={showUpload} onOpenChange={setShowUpload}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Upload Resume</DialogTitle>
          </DialogHeader>
          <ResumeUpload onSuccess={() => setShowUpload(false)} />
        </DialogContent>
      </Dialog>

      {/* Upload zone (always visible on empty) */}
      {!isLoading && (!resumes || resumes.length === 0) && (
        <div className="rounded-xl border-2 border-dashed border-border p-8">
          <EmptyState
            icon={FileUser}
            title="No resumes yet"
            description="Upload your master resume to get started. JobSense will parse it and create tailored versions for each job."
            action={{ label: 'Upload Resume', onClick: () => setShowUpload(true) }}
          />
        </div>
      )}

      {/* Resume grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : resumes && resumes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resumes.map((resume) => (
            <ResumeCard key={resume.id} resume={resume} />
          ))}
        </div>
      ) : null}
    </div>
  )
}
