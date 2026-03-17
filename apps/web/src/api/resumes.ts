import type { MasterResume, ResumeVersion, TailoringRequest } from '@applyflow/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export async function getResumesApi(): Promise<MasterResume[]> {
  const response = await apiClient.get<MasterResume[]>(API_ROUTES.RESUMES)
  return response.data
}

export async function getResumeByIdApi(id: string): Promise<MasterResume> {
  const response = await apiClient.get<MasterResume>(API_ROUTES.RESUME_BY_ID(id))
  return response.data
}

export async function uploadResumeApi(
  file: File,
  name: string,
  onProgress?: (pct: number) => void
): Promise<MasterResume> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)

  const response = await apiClient.post<MasterResume>(API_ROUTES.RESUME_UPLOAD, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
  return response.data
}

export async function deleteResumeApi(id: string): Promise<void> {
  await apiClient.delete(API_ROUTES.RESUME_BY_ID(id))
}

export async function getResumeVersionsApi(id: string): Promise<ResumeVersion[]> {
  const response = await apiClient.get<ResumeVersion[]>(API_ROUTES.RESUME_VERSIONS(id))
  return response.data
}

export async function tailorResumeApi(data: TailoringRequest): Promise<ResumeVersion> {
  const response = await apiClient.post<ResumeVersion>(API_ROUTES.RESUME_TAILOR, data)
  return response.data
}

export async function setActiveResumeApi(id: string): Promise<MasterResume> {
  const response = await apiClient.post<MasterResume>(`${API_ROUTES.RESUME_BY_ID(id)}/activate`)
  return response.data
}
