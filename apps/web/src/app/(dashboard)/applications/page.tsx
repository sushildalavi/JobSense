'use client'

import { useState } from 'react'
import { Plus, LayoutGrid, List, FileText } from 'lucide-react'
import { useApplications } from '@/hooks/use-applications'
import { ApplicationTable } from '@/components/applications/application-table'
import { KanbanBoard } from '@/components/applications/kanban-board'
import { PageHeader } from '@/components/common/page-header'
import { EmptyState } from '@/components/common/empty-state'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import Link from 'next/link'

type ViewMode = 'table' | 'kanban'

export default function ApplicationsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const { data: applications, isLoading, isError } = useApplications()

  const count = applications?.length || 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        badge={<Badge variant="muted" className="text-xs">{count} total</Badge>}
        subtitle="Track and manage your job applications"
        action={
          <div className="flex items-center gap-2">
            {/* View toggle */}
            <div className="flex items-center rounded-lg border border-border p-0.5">
              <button
                onClick={() => setViewMode('table')}
                className={`p-1.5 rounded-md transition-colors ${
                  viewMode === 'table'
                    ? 'bg-card text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`p-1.5 rounded-md transition-colors ${
                  viewMode === 'kanban'
                    ? 'bg-card text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
            <Button asChild size="sm">
              <Link href="/jobs">
                <Plus className="w-4 h-4 mr-2" />
                Add Application
              </Link>
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : isError ? (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          Failed to load applications.
        </div>
      ) : !applications || applications.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No applications yet"
          description="Start tracking your job applications by exploring jobs or adding them manually."
          action={{ label: 'Browse Jobs', onClick: () => {} }}
        />
      ) : viewMode === 'table' ? (
        <ApplicationTable applications={applications} />
      ) : (
        <KanbanBoard applications={applications} />
      )}
    </div>
  )
}
