'use client'

import { useState } from 'react'
import { RefreshCw, Mail, X } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getEmailThreadsApi, syncEmailsApi } from '@/api/emails'
import { QUERY_KEYS } from '@/lib/constants'
import type { EmailClassification, EmailThread } from '@applyflow/types'
import { EmailThreadCard } from '@/components/emails/email-thread-card'
import { PageHeader } from '@/components/common/page-header'
import { EmptyState } from '@/components/common/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import { queryClient } from '@/lib/query-client'

const classificationFilters: { label: string; value: EmailClassification | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Recruiter', value: 'recruiter_outreach' },
  { label: 'Interview', value: 'interview_scheduling' },
  { label: 'OA', value: 'oa_assessment' },
  { label: 'Rejection', value: 'rejection' },
  { label: 'Offer', value: 'offer' },
]

export default function EmailsPage() {
  const [filter, setFilter] = useState<EmailClassification | 'all'>('all')
  const [selectedThread, setSelectedThread] = useState<EmailThread | null>(null)

  const { data: threads, isLoading } = useQuery({
    queryKey: [QUERY_KEYS.EMAIL_THREADS, filter],
    queryFn: () =>
      getEmailThreadsApi(filter !== 'all' ? { classification: filter } : undefined),
  })

  const { mutate: syncEmails, isPending: syncing } = useMutation({
    mutationFn: syncEmailsApi,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.EMAIL_THREADS] })
      toast.success(`Synced: ${data.threads_processed} emails processed`)
    },
    onError: () => toast.error('Failed to sync emails'),
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Email Intelligence"
        subtitle="AI-parsed email threads from your job search"
        action={
          <Button onClick={() => syncEmails()} loading={syncing} size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Sync Gmail
          </Button>
        }
      />

      {/* Classification filters */}
      <div className="flex flex-wrap gap-2">
        {classificationFilters.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
              filter === f.value
                ? 'bg-primary/20 text-primary border-primary/30'
                : 'border-border text-muted-foreground hover:border-primary/30 hover:text-foreground'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* Thread list */}
        <div className="flex-1 space-y-3">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24" />)
          ) : !threads || threads.length === 0 ? (
            <EmptyState
              icon={Mail}
              title="No email threads"
              description="Sync your Gmail to see AI-classified email threads from recruiters and companies."
              action={{ label: 'Sync Gmail', onClick: () => syncEmails() }}
            />
          ) : (
            threads.map((thread) => (
              <EmailThreadCard
                key={thread.id}
                thread={thread}
                onClick={() => setSelectedThread(thread)}
              />
            ))
          )}
        </div>

        {/* Thread detail panel */}
        {selectedThread && (
          <div className="w-96 shrink-0">
            <Card className="sticky top-20">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base line-clamp-2">{selectedThread.subject}</CardTitle>
                  <Button
                    size="icon-sm"
                    variant="ghost"
                    onClick={() => setSelectedThread(null)}
                    className="shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Classification</span>
                    <span className="font-medium capitalize">
                      {selectedThread.classification.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Confidence</span>
                    <span className="font-medium">
                      {Math.round(selectedThread.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Messages</span>
                    <span className="font-medium">{selectedThread.message_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last activity</span>
                    <span className="font-medium">{formatDate(selectedThread.last_message_at)}</span>
                  </div>
                </div>

                <Separator />

                {/* Participants */}
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Participants</p>
                  <div className="space-y-1">
                    {selectedThread.participants.map((p, i) => (
                      <p key={i} className="text-xs text-foreground">{p}</p>
                    ))}
                  </div>
                </div>

                {/* Parsed emails */}
                {selectedThread.parsed_emails && selectedThread.parsed_emails.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-xs text-muted-foreground mb-3">Extracted Data</p>
                      {selectedThread.parsed_emails.slice(0, 1).map((email) => (
                        <div key={email.id} className="space-y-2 text-xs">
                          {email.extracted_company && (
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Company</span>
                              <span className="font-medium">{email.extracted_company}</span>
                            </div>
                          )}
                          {email.extracted_job_title && (
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Role</span>
                              <span className="font-medium">{email.extracted_job_title}</span>
                            </div>
                          )}
                          {email.extracted_interviewer_name && (
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Interviewer</span>
                              <span className="font-medium">{email.extracted_interviewer_name}</span>
                            </div>
                          )}
                          {email.extracted_interview_datetime && (
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Date</span>
                              <span className="font-medium">
                                {formatDate(email.extracted_interview_datetime, 'MMM d, h:mm a')}
                              </span>
                            </div>
                          )}
                          {email.extracted_meeting_link && (
                            <div>
                              <span className="text-muted-foreground block mb-1">Meeting</span>
                              <a
                                href={email.extracted_meeting_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline break-all"
                              >
                                {email.extracted_meeting_link}
                              </a>
                            </div>
                          )}
                          {email.extracted_next_action && (
                            <div>
                              <span className="text-muted-foreground block mb-1">Next Action</span>
                              <p className="text-foreground">{email.extracted_next_action}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
