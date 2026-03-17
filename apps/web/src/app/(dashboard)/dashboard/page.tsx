'use client'

import Link from 'next/link'
import { Briefcase, FileText, Calendar, TrendingUp, RefreshCw, Upload, Plus } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/use-auth'
import { useDashboardStats, useAnalyticsSummary } from '@/hooks/use-analytics'
import { useApplications } from '@/hooks/use-applications'
import { useJobs, useSyncJobs } from '@/hooks/use-jobs'
import { MetricCard } from '@/components/analytics/metric-card'
import { FunnelChart } from '@/components/analytics/funnel-chart'
import { WeeklyChart } from '@/components/analytics/weekly-chart'
import { JobCard } from '@/components/jobs/job-card'
import { StatusBadge } from '@/components/applications/status-badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { PageHeader } from '@/components/common/page-header'
import { formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: analytics, isLoading: analyticsLoading } = useAnalyticsSummary()
  const { data: applicationsData, isLoading: appsLoading } = useApplications()
  const { data: jobsData, isLoading: jobsLoading } = useJobs({ limit: 3, min_match_score: 60 })
  const { mutate: syncJobs, isPending: syncing } = useSyncJobs()

  const firstName = user?.full_name?.split(' ')[0] || 'there'

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back, ${firstName}!`}
        subtitle="Here's your job search overview"
        action={
          <Button onClick={() => syncJobs()} loading={syncing} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Sync Jobs
          </Button>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)
        ) : (
          <>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <MetricCard
                title="Jobs Discovered"
                value={stats?.total_jobs_discovered ?? 0}
                icon={Briefcase}
                color="indigo"
                subtitle="Total matched jobs"
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
              <MetricCard
                title="Applications Sent"
                value={stats?.total_applied ?? 0}
                icon={FileText}
                color="violet"
                subtitle={`${stats?.active_applications ?? 0} active`}
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <MetricCard
                title="Interviews"
                value={stats?.total_interviews ?? 0}
                icon={Calendar}
                color="emerald"
                subtitle={`${stats?.interview_rate ? (stats.interview_rate * 100).toFixed(1) : 0}% rate`}
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              <MetricCard
                title="Offer Rate"
                value={`${stats?.offer_rate ? (stats.offer_rate * 100).toFixed(1) : 0}%`}
                icon={TrendingUp}
                color="amber"
                subtitle={`${stats?.total_offers ?? 0} total offers`}
              />
            </motion.div>
          </>
        )}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {analyticsLoading ? (
          <>
            <Skeleton className="h-80" />
            <Skeleton className="h-80" />
          </>
        ) : (
          <>
            {analytics?.funnel && <FunnelChart data={analytics.funnel} />}
            {analytics?.weekly_activity && <WeeklyChart data={analytics.weekly_activity} />}
          </>
        )}
      </div>

      {/* Bottom row: Recent applications + Top jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent applications */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Recent Applications</CardTitle>
                <Button asChild variant="ghost" size="sm" className="text-xs">
                  <Link href="/applications">View all</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {appsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : !applicationsData?.length ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No applications yet.{' '}
                  <Link href="/jobs" className="text-primary hover:underline">
                    Start exploring jobs
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {applicationsData.slice(0, 5).map((app) => (
                    <Link
                      key={app.id}
                      href={`/applications/${app.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div>
                        <p className="text-sm font-medium text-foreground">{app.company_name}</p>
                        <p className="text-xs text-muted-foreground">{app.job_title}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={app.status} />
                        <span className="text-xs text-muted-foreground hidden sm:block">
                          {formatDate(app.created_at, 'MMM d')}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick actions */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button asChild variant="outline" className="w-full justify-start gap-2">
                <Link href="/jobs">
                  <Briefcase className="w-4 h-4" />
                  Browse Jobs
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start gap-2">
                <Link href="/resumes">
                  <Upload className="w-4 h-4" />
                  Upload Resume
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start gap-2">
                <Link href="/applications">
                  <Plus className="w-4 h-4" />
                  Add Application
                </Link>
              </Button>
              <Button asChild variant="outline" className="w-full justify-start gap-2">
                <Link href="/emails">
                  <RefreshCw className="w-4 h-4" />
                  Sync Emails
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Top matched jobs */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Top Matches</CardTitle>
                <Button asChild variant="ghost" size="sm" className="text-xs">
                  <Link href="/jobs">See all</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {jobsLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
                </div>
              ) : jobsData?.items.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">
                  Sync jobs to see matches
                </p>
              ) : (
                <div className="space-y-3">
                  {jobsData?.items.slice(0, 3).map((job) => (
                    <Link
                      key={job.id}
                      href={`/jobs/${job.id}`}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{job.title}</p>
                        <p className="text-xs text-muted-foreground truncate">{job.company_name}</p>
                      </div>
                      {job.match_score && (
                        <span className="text-xs font-bold text-primary shrink-0">
                          {Math.round(job.match_score)}%
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
