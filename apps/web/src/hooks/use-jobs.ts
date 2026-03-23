'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { JobFilter } from '@jobsense/types'
import { getJobsApi, getJobByIdApi, shortlistJobApi, syncJobsApi } from '@/api/jobs'
import { QUERY_KEYS } from '@/lib/constants'
import { toast } from 'sonner'

export function useJobs(filters?: JobFilter) {
  return useQuery({
    queryKey: [QUERY_KEYS.JOBS, filters],
    queryFn: () => getJobsApi(filters),
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: [QUERY_KEYS.JOB, id],
    queryFn: () => getJobByIdApi(id),
    enabled: !!id,
  })
}

export function useShortlistJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: shortlistJobApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.JOBS] })
      toast.success('Job shortlisted successfully')
    },
    onError: () => {
      toast.error('Failed to shortlist job')
    },
  })
}

export function useSyncJobs() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: syncJobsApi,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.JOBS] })
      toast.success(`Sync complete: ${data.jobs_added} new jobs discovered`)
    },
    onError: () => {
      toast.error('Failed to sync jobs')
    },
  })
}
