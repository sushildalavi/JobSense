'use client'

import { useState } from 'react'
import { RefreshCw, SortAsc, Briefcase } from 'lucide-react'
import type { JobFilter } from '@applyflow/types'
import { useJobs, useSyncJobs } from '@/hooks/use-jobs'
import { JobCard } from '@/components/jobs/job-card'
import { JobFilters } from '@/components/jobs/job-filters'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { PageHeader } from '@/components/common/page-header'
import { EmptyState } from '@/components/common/empty-state'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { motion, AnimatePresence } from 'framer-motion'

export default function JobsPage() {
  const [filters, setFilters] = useState<JobFilter>({ limit: 24, skip: 0 })
  const [sortBy, setSortBy] = useState<'match_score' | 'date'>('match_score')

  const { data, isLoading, isError } = useJobs(filters)
  const { mutate: syncJobs, isPending: syncing } = useSyncJobs()

  const jobs = data?.items || []
  const total = data?.total || 0

  const sortedJobs = [...jobs].sort((a, b) => {
    if (sortBy === 'match_score') {
      return (b.match_score || 0) - (a.match_score || 0)
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Discovered Jobs"
        badge={<Badge variant="muted" className="text-xs">{total} jobs</Badge>}
        subtitle="AI-curated jobs matched to your profile"
        action={
          <div className="flex items-center gap-2">
            <Select value={sortBy} onValueChange={(v) => setSortBy(v as typeof sortBy)}>
              <SelectTrigger className="w-40 h-9 text-sm">
                <SortAsc className="w-3.5 h-3.5 mr-1.5 text-muted-foreground" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="match_score">Best Match</SelectItem>
                <SelectItem value="date">Most Recent</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={() => syncJobs()} loading={syncing} size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Sync Jobs
            </Button>
          </div>
        }
      />

      <div className="flex gap-6">
        {/* Filters sidebar */}
        <div className="w-64 shrink-0">
          <div className="sticky top-20">
            <JobFilters filters={filters} onChange={(f) => setFilters({ ...f, skip: 0 })} />
          </div>
        </div>

        {/* Jobs grid */}
        <div className="flex-1">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 9 }).map((_, i) => (
                <Skeleton key={i} className="h-64" />
              ))}
            </div>
          ) : isError ? (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              Failed to load jobs. Please try again.
            </div>
          ) : sortedJobs.length === 0 ? (
            <EmptyState
              icon={Briefcase}
              title="No jobs found"
              description="Try adjusting your filters or sync new jobs to see more matches."
              action={{ label: 'Sync Jobs', onClick: () => syncJobs() }}
            />
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                <AnimatePresence>
                  {sortedJobs.map((job, i) => (
                    <motion.div
                      key={job.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.04, duration: 0.3 }}
                    >
                      <JobCard job={job} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Pagination */}
              {total > (filters.limit || 24) && (
                <div className="flex items-center justify-center gap-3 mt-8">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!filters.skip || filters.skip === 0}
                    onClick={() => setFilters((f) => ({ ...f, skip: Math.max(0, (f.skip || 0) - (f.limit || 24)) }))}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {Math.floor((filters.skip || 0) / (filters.limit || 24)) + 1} of{' '}
                    {Math.ceil(total / (filters.limit || 24))}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(filters.skip || 0) + (filters.limit || 24) >= total}
                    onClick={() => setFilters((f) => ({ ...f, skip: (f.skip || 0) + (f.limit || 24) }))}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
