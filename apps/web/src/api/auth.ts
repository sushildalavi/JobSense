import type { User, TokenResponse, LoginRequest, RegisterRequest } from '@jobsense/types'
import apiClient from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export async function loginApi(data: LoginRequest): Promise<TokenResponse> {
  const formData = new URLSearchParams()
  formData.append('username', data.email)
  formData.append('password', data.password)

  const response = await apiClient.post<TokenResponse>(API_ROUTES.AUTH_LOGIN, formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

export async function registerApi(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>(API_ROUTES.AUTH_REGISTER, data)
  return response.data
}

export async function getMeApi(): Promise<User> {
  const response = await apiClient.get<User>(API_ROUTES.AUTH_ME)
  return response.data
}

export async function logoutApi(): Promise<void> {
  await apiClient.post(API_ROUTES.AUTH_LOGOUT)
}
