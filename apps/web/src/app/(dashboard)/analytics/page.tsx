'use client'

import {
  BarChart2,
  Briefcase,
  FileText,
  Calendar,
  TrendingUp,
  Target,
  Users,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts'
import { useAnalyticsSummary, useDashboardStats } from '@/hooks/use-analytics'
import { MetricCard } from '@/components/analytics/metric-card'
import { FunnelChart } from '@/components/analytics/funnel-chart'
import { WeeklyChart } from '@/components/analytics/weekly-chart'
import { PageHeader } from '@/components/common/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#64748b']

export default function AnalyticsPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: analytics, isLoading: analyticsLoading } = useAnalyticsSummary()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        subtitle="Insights into your job search performance"
      />

      {/* Metrics row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)
        ) : (
          <>
            <MetricCard
              title="Total Applications"
              value={stats?.total_applied ?? 0}
              icon={FileText}
              color="indigo"
            />
            <MetricCard
              title="Active Pipeline"
              value={stats?.active_applications ?? 0}
              icon={Briefcase}
              color="violet"
            />
            <MetricCard
              title="Interview Rate"
              value={`${stats?.interview_rate ? (stats.interview_rate * 100).toFixed(1) : 0}%`}
              icon={Calendar}
              color="emerald"
            />
            <MetricCard
              title="Offer Rate"
              value={`${stats?.offer_rate ? (stats.offer_rate * 100).toFixed(1) : 0}%`}
              icon={TrendingUp}
              color="amber"
            />
          </>
        )}
      </div>

      {/* Second row metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {statsLoading ? (
          Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)
        ) : (
          <>
            <MetricCard
              title="Response Rate"
              value={`${stats?.response_rate ? (stats.response_rate * 100).toFixed(1) : 0}%`}
              icon={Users}
              color="cyan"
              subtitle="Responses received"
            />
            <MetricCard
              title="Total Rejections"
              value={stats?.total_rejections ?? 0}
              icon={Target}
              color="red"
              subtitle="Learning opportunities"
            />
            <MetricCard
              title="Total Offers"
              value={stats?.total_offers ?? 0}
              icon={TrendingUp}
              color="emerald"
              subtitle="Congratulations!"
            />
          </>
        )}
      </div>

      {/* Charts */}
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

      {/* Bottom row: score distribution + source breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Match Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Match Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {analyticsLoading ? (
              <Skeleton className="h-64" />
            ) : analytics?.match_score_distribution ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={analytics.match_score_distribution} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                  <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111118',
                      border: '1px solid #1e1e2e',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {analytics.match_score_distribution.map((entry, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">No data available</p>
            )}
          </CardContent>
        </Card>

        {/* Source Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Jobs by Source</CardTitle>
          </CardHeader>
          <CardContent>
            {analyticsLoading ? (
              <Skeleton className="h-64" />
            ) : analytics?.by_source && analytics.by_source.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={analytics.by_source}
                    dataKey="count"
                    nameKey="source"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    labelLine={false}
                  >
                    {analytics.by_source.map((entry, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111118',
                      border: '1px solid #1e1e2e',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: '12px', color: '#64748b' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">No data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
