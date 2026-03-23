'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { WeeklyStat } from '@jobsense/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface WeeklyChartProps {
  data: WeeklyStat[]
}

export function WeeklyChart({ data }: WeeklyChartProps) {
  const chartData = data.map((s) => ({
    week: s.week,
    Applications: s.applications,
    Interviews: s.interviews,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Weekly Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
            <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
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
            <Line
              type="monotone"
              dataKey="Applications"
              stroke="#6366f1"
              strokeWidth={2}
              dot={{ fill: '#6366f1', r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Interviews"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
