'use client'

import { useState } from 'react'
import { ExternalLink, MapPin } from 'lucide-react'
import type { Application, ApplicationEvent } from '@applyflow/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { StatusBadge } from './status-badge'
import { formatDate, formatRelativeDate } from '@/lib/utils'
import { useUpdateApplication, useUpdateApplicationStatus } from '@/hooks/use-applications'
import { STATUS_LABELS } from '@/lib/constants'
import type { ApplicationStatus } from '@applyflow/types'

interface ApplicationDetailProps {
  application: Application
  events?: ApplicationEvent[]
}

const NEXT_STATUSES: Partial<Record<ApplicationStatus, ApplicationStatus[]>> = {
  shortlisted: ['tailored', 'archived'],
  tailored: ['ready_to_apply', 'archived'],
  ready_to_apply: ['applied', 'archived'],
  applied: ['oa_received', 'recruiter_contacted', 'interview_scheduled', 'rejected', 'archived'],
  oa_received: ['interview_scheduled', 'rejected', 'archived'],
  recruiter_contacted: ['interview_scheduled', 'rejected', 'archived'],
  interview_scheduled: ['offer', 'rejected', 'archived'],
}

export function ApplicationDetail({ application, events = [] }: ApplicationDetailProps) {
  const [notes, setNotes] = useState(application.notes || '')
  const [editingNotes, setEditingNotes] = useState(false)
  const { mutate: updateApp } = useUpdateApplication()
  const { mutate: updateStatus, isPending: statusPending } = useUpdateApplicationStatus()

  const nextStatuses = NEXT_STATUSES[application.status] || []

  const saveNotes = () => {
    updateApp({ id: application.id, data: { notes } })
    setEditingNotes(false)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main info */}
      <div className="lg:col-span-2 space-y-6">
        {/* Header card */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-foreground">
                  {application.job?.title || 'Unknown Role'}
                </h2>
                <p className="text-lg text-muted-foreground mt-1">
                  {application.job?.company_name || '—'}
                </p>
                <div className="flex items-center gap-3 mt-3 flex-wrap">
                  <StatusBadge status={application.status} />
                  {application.job?.location && (
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <MapPin className="w-3 h-3" />
                      {application.job.location}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground">
                    Added {formatRelativeDate(application.created_at)}
                  </span>
                </div>
              </div>
              {application.application_url && (
                <Button size="sm" asChild variant="outline">
                  <a href={application.application_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View Posting
                  </a>
                </Button>
              )}
            </div>

            {/* Status transitions */}
            {nextStatuses.length > 0 && (
              <div className="mt-6">
                <p className="text-xs text-muted-foreground mb-2">Move to:</p>
                <div className="flex flex-wrap gap-2">
                  {nextStatuses.map((s) => (
                    <Button
                      key={s}
                      size="sm"
                      variant="outline"
                      disabled={statusPending}
                      onClick={() => updateStatus({ id: application.id, status: s })}
                      className="text-xs"
                    >
                      {STATUS_LABELS[s]}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Notes</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => (editingNotes ? saveNotes() : setEditingNotes(true))}
              >
                {editingNotes ? 'Save' : 'Edit'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {editingNotes ? (
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about this application..."
                className="min-h-[120px]"
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                {notes || 'No notes yet. Click Edit to add notes.'}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sidebar: timeline + metadata */}
      <div className="space-y-6">
        {/* Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No events yet</p>
            ) : (
              <div className="relative">
                <div className="absolute left-2.5 top-0 bottom-0 w-px bg-border" />
                <div className="space-y-4">
                  {events.map((event, i) => (
                    <div key={event.id} className="flex gap-3 pl-7 relative">
                      <div className="absolute left-0 top-1 w-5 h-5 rounded-full bg-card border-2 border-primary flex items-center justify-center">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {event.to_status ? STATUS_LABELS[event.to_status] : '—'}
                        </p>
                        {event.notes && (
                          <p className="text-xs text-muted-foreground mt-0.5">{event.notes}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatRelativeDate(event.created_at)} · by {event.triggered_by}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">Applied on</p>
              <p className="text-sm font-medium">{formatDate(application.applied_at) || '—'}</p>
            </div>
            <Separator />
            <div>
              <p className="text-xs text-muted-foreground">Source</p>
              <p className="text-sm font-medium">{application.source_of_discovery || '—'}</p>
            </div>
            <Separator />
            <div>
              <p className="text-xs text-muted-foreground">Resume version</p>
              <p className="text-sm font-medium">
                {application.resume_version_id ? 'Tailored version' : 'No resume attached'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
