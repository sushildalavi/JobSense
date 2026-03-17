import type { EmailThread, EmailClassification } from '@applyflow/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface EmailThreadsFilter {
  classification?: EmailClassification
  skip?: number
  limit?: number
}

export async function getEmailThreadsApi(filters?: EmailThreadsFilter): Promise<EmailThread[]> {
  const response = await apiClient.get<EmailThread[]>(API_ROUTES.EMAIL_THREADS, {
    params: filters,
  })
  return response.data
}

export async function getEmailThreadByIdApi(id: string): Promise<EmailThread> {
  const response = await apiClient.get<EmailThread>(API_ROUTES.EMAIL_THREAD_BY_ID(id))
  return response.data
}

export async function syncEmailsApi(): Promise<{ message: string; threads_processed: number }> {
  const response = await apiClient.post<{ message: string; threads_processed: number }>(
    API_ROUTES.EMAIL_SYNC
  )
  return response.data
}
