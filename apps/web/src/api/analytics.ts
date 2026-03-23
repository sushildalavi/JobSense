import type { AnalyticsSummary, DashboardStats } from '@jobsense/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export async function getAnalyticsSummaryApi(): Promise<AnalyticsSummary> {
  const response = await apiClient.get<AnalyticsSummary>(API_ROUTES.ANALYTICS_SUMMARY)
  return response.data
}

export async function getDashboardStatsApi(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>(API_ROUTES.DASHBOARD_STATS)
  return response.data
}
