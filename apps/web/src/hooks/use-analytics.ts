'use client'

import { useQuery } from '@tanstack/react-query'
import { getAnalyticsSummaryApi, getDashboardStatsApi } from '@/api/analytics'
import { QUERY_KEYS } from '@/lib/constants'

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS],
    queryFn: getAnalyticsSummaryApi,
    staleTime: 1000 * 60 * 5,
  })
}

export function useDashboardStats() {
  return useQuery({
    queryKey: [QUERY_KEYS.DASHBOARD_STATS],
    queryFn: getDashboardStatsApi,
    staleTime: 1000 * 60 * 2,
  })
}
