import type { CalendarEvent } from '@applyflow/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface CreateCalendarEventPayload {
  application_id?: string
  title: string
  description?: string
  start_datetime: string
  end_datetime: string
  timezone: string
  meeting_link?: string
  location?: string
}

export async function getCalendarEventsApi(): Promise<CalendarEvent[]> {
  const response = await apiClient.get<CalendarEvent[]>(API_ROUTES.CALENDAR_EVENTS)
  return response.data
}

export async function getCalendarEventByIdApi(id: string): Promise<CalendarEvent> {
  const response = await apiClient.get<CalendarEvent>(API_ROUTES.CALENDAR_EVENT_BY_ID(id))
  return response.data
}

export async function createCalendarEventApi(
  data: CreateCalendarEventPayload
): Promise<CalendarEvent> {
  const response = await apiClient.post<CalendarEvent>(API_ROUTES.CALENDAR_EVENTS, data)
  return response.data
}

export async function syncCalendarApi(): Promise<{ message: string; events_synced: number }> {
  const response = await apiClient.post<{ message: string; events_synced: number }>(
    API_ROUTES.CALENDAR_SYNC
  )
  return response.data
}

export async function deleteCalendarEventApi(id: string): Promise<void> {
  await apiClient.delete(API_ROUTES.CALENDAR_EVENT_BY_ID(id))
}
