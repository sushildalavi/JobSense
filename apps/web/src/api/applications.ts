import type {
  Application,
  ApplicationListItem,
  ApplicationStatus,
  ApplicationEvent,
} from '@applyflow/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface CreateApplicationPayload {
  job_id: string
  resume_version_id?: string
  notes?: string
}

export interface UpdateApplicationPayload {
  notes?: string
  cover_letter?: string
  resume_version_id?: string
}

export async function getApplicationsApi(): Promise<ApplicationListItem[]> {
  const response = await apiClient.get<ApplicationListItem[]>(API_ROUTES.APPLICATIONS)
  return response.data
}

export async function getApplicationByIdApi(id: string): Promise<Application> {
  const response = await apiClient.get<Application>(API_ROUTES.APPLICATION_BY_ID(id))
  return response.data
}

export async function createApplicationApi(data: CreateApplicationPayload): Promise<Application> {
  const response = await apiClient.post<Application>(API_ROUTES.APPLICATIONS, data)
  return response.data
}

export async function updateApplicationApi(
  id: string,
  data: UpdateApplicationPayload
): Promise<Application> {
  const response = await apiClient.patch<Application>(API_ROUTES.APPLICATION_BY_ID(id), data)
  return response.data
}

export async function updateApplicationStatusApi(
  id: string,
  status: ApplicationStatus,
  notes?: string
): Promise<Application> {
  const response = await apiClient.post<Application>(API_ROUTES.APPLICATION_STATUS(id), {
    status,
    notes,
  })
  return response.data
}

export async function getApplicationEventsApi(id: string): Promise<ApplicationEvent[]> {
  const response = await apiClient.get<ApplicationEvent[]>(API_ROUTES.APPLICATION_EVENTS(id))
  return response.data
}

export async function deleteApplicationApi(id: string): Promise<void> {
  await apiClient.delete(API_ROUTES.APPLICATION_BY_ID(id))
}
