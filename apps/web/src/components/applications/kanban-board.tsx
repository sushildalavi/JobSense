'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { ApplicationListItem, ApplicationStatus } from '@applyflow/types'
import { StatusBadge } from './status-badge'
import { formatDate } from '@/lib/utils'
import { STATUS_LABELS, STATUS_DOT_COLORS } from '@/lib/constants'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface KanbanBoardProps {
  applications: ApplicationListItem[]
}

const KANBAN_COLUMNS: ApplicationStatus[] = [
  'shortlisted',
  'applied',
  'oa_received',
  'recruiter_contacted',
  'interview_scheduled',
  'offer',
  'rejected',
]

export function KanbanBoard({ applications }: KanbanBoardProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null)

  const getColumnApps = (status: ApplicationStatus) =>
    applications.filter((a) => a.status === status)

  return (
    <div className="flex gap-4 overflow-x-auto pb-4 -mx-1 px-1">
      {KANBAN_COLUMNS.map((status) => {
        const columnApps = getColumnApps(status)
        return (
          <div
            key={status}
            className="flex-shrink-0 w-[260px] flex flex-col rounded-xl border border-border bg-card/50"
          >
            {/* Column header */}
            <div className="flex items-center justify-between p-3 border-b border-border">
              <div className="flex items-center gap-2">
                <div className={cn('w-2 h-2 rounded-full', STATUS_DOT_COLORS[status])} />
                <span className="text-sm font-medium">{STATUS_LABELS[status]}</span>
              </div>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                {columnApps.length}
              </span>
            </div>

            {/* Cards */}
            <ScrollArea className="flex-1 max-h-[calc(100vh-280px)]">
              <div className="p-2 space-y-2">
                {columnApps.length === 0 ? (
                  <div className="py-8 text-center text-xs text-muted-foreground">
                    No applications
                  </div>
                ) : (
                  columnApps.map((app) => (
                    <Link
                      key={app.id}
                      href={`/applications/${app.id}`}
                      draggable
                      onDragStart={() => setDraggedId(app.id)}
                      onDragEnd={() => setDraggedId(null)}
                      className={cn(
                        'block p-3 rounded-lg border border-border bg-card hover:border-primary/30 hover:bg-muted/50 transition-all cursor-pointer',
                        draggedId === app.id && 'opacity-50'
                      )}
                    >
                      <p className="font-medium text-sm text-foreground line-clamp-1">
                        {app.company_name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                        {app.job_title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDate(app.applied_at || app.created_at, 'MMM d')}
                      </p>
                    </Link>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        )
      })}
    </div>
  )
}
