import type { Job, JobListItem, JobFilter, JobMatch } from '@applyflow/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface PaginatedJobs {
  items: JobListItem[]
  total: number
  skip: number
  limit: number
}

export async function getJobsApi(filters?: JobFilter): Promise<PaginatedJobs> {
  const response = await apiClient.get<PaginatedJobs>(API_ROUTES.JOBS, { params: filters })
  return response.data
}

export async function getJobByIdApi(id: string): Promise<Job> {
  const response = await apiClient.get<Job>(API_ROUTES.JOB_BY_ID(id))
  return response.data
}

export async function shortlistJobApi(id: string): Promise<void> {
  await apiClient.post(API_ROUTES.JOB_SHORTLIST(id))
}

export async function getJobMatchApi(id: string): Promise<JobMatch> {
  const response = await apiClient.get<JobMatch>(API_ROUTES.JOB_MATCH(id))
  return response.data
}

export async function syncJobsApi(): Promise<{ message: string; jobs_added: number }> {
  const response = await apiClient.post<{ message: string; jobs_added: number }>(
    API_ROUTES.JOBS_SYNC
  )
  return response.data
}
