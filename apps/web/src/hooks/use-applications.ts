'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { ApplicationStatus } from '@applyflow/types'
import {
  getApplicationsApi,
  getApplicationByIdApi,
  createApplicationApi,
  updateApplicationApi,
  updateApplicationStatusApi,
  getApplicationEventsApi,
  deleteApplicationApi,
  type CreateApplicationPayload,
  type UpdateApplicationPayload,
} from '@/api/applications'
import { QUERY_KEYS } from '@/lib/constants'
import { toast } from 'sonner'

export function useApplications() {
  return useQuery({
    queryKey: [QUERY_KEYS.APPLICATIONS],
    queryFn: getApplicationsApi,
  })
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: [QUERY_KEYS.APPLICATION, id],
    queryFn: () => getApplicationByIdApi(id),
    enabled: !!id,
  })
}

export function useApplicationEvents(id: string) {
  return useQuery({
    queryKey: [QUERY_KEYS.APPLICATION_EVENTS, id],
    queryFn: () => getApplicationEventsApi(id),
    enabled: !!id,
  })
}

export function useCreateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateApplicationPayload) => createApplicationApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATIONS] })
      toast.success('Application created')
    },
    onError: () => {
      toast.error('Failed to create application')
    },
  })
}

export function useUpdateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateApplicationPayload }) =>
      updateApplicationApi(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATION, id] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATIONS] })
      toast.success('Application updated')
    },
    onError: () => {
      toast.error('Failed to update application')
    },
  })
}

export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      status,
      notes,
    }: {
      id: string
      status: ApplicationStatus
      notes?: string
    }) => updateApplicationStatusApi(id, status, notes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATION, id] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATIONS] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATION_EVENTS, id] })
      toast.success('Status updated')
    },
    onError: () => {
      toast.error('Failed to update status')
    },
  })
}

export function useDeleteApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteApplicationApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.APPLICATIONS] })
      toast.success('Application deleted')
    },
    onError: () => {
      toast.error('Failed to delete application')
    },
  })
}
