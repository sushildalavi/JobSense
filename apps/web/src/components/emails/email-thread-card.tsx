'use client'

import { Mail, Users, ExternalLink } from 'lucide-react'
import type { EmailThread, EmailClassification } from '@applyflow/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatRelativeDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface EmailThreadCardProps {
  thread: EmailThread
  onClick?: () => void
}

const classificationConfig: Record<
  EmailClassification,
  { label: string; color: string }
> = {
  recruiter_outreach: { label: 'Recruiter', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  oa_assessment: { label: 'OA', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' },
  interview_scheduling: { label: 'Interview', color: 'bg-green-500/20 text-green-300 border-green-500/30' },
  interview_confirmation: { label: 'Confirmed', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  rejection: { label: 'Rejection', color: 'bg-red-500/20 text-red-300 border-red-500/30' },
  offer: { label: 'Offer!', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  follow_up: { label: 'Follow-up', color: 'bg-orange-500/20 text-orange-300 border-orange-500/30' },
  noise: { label: 'Noise', color: 'bg-slate-500/20 text-slate-300 border-slate-500/30' },
  unclassified: { label: 'Unclassified', color: 'bg-gray-500/20 text-gray-300 border-gray-500/30' },
}

export function EmailThreadCard({ thread, onClick }: EmailThreadCardProps) {
  const config = classificationConfig[thread.classification]
  const confidencePct = Math.round(thread.confidence_score * 100)

  return (
    <Card
      className="group cursor-pointer hover:border-primary/30 hover:bg-muted/20 transition-all"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
            <Mail className="w-4 h-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-medium text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                {thread.subject}
              </h4>
              <span className="text-xs text-muted-foreground shrink-0">
                {formatRelativeDate(thread.last_message_at)}
              </span>
            </div>

            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <span
                className={cn(
                  'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border',
                  config.color
                )}
              >
                {config.label}
              </span>
              <span className="text-xs text-muted-foreground">
                {confidencePct}% confidence
              </span>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Users className="w-3 h-3" />
                {thread.message_count} messages
              </span>
            </div>

            {thread.participants.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1.5 truncate">
                {thread.participants.slice(0, 2).join(', ')}
                {thread.participants.length > 2 && ` +${thread.participants.length - 2} more`}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
