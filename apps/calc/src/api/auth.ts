import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest, ensureCsrf } from './client'

export type CurrentUser = {
  user_id: number
  email: string
  display_name: string
}

export type LoginValues = {
  email: string
  password: string
}

export type RegisterValues = LoginValues & {
  password_confirm: string
}

export const AUTH_QUERY_KEY = ['auth', 'me'] as const

export async function fetchCurrentUser() {
  return apiRequest<CurrentUser>('/auth/me', {}, { suppressUnauthorizedEvent: true })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: AUTH_QUERY_KEY,
    queryFn: fetchCurrentUser,
    retry: false,
    staleTime: 60 * 1000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (values: LoginValues) => {
      await ensureCsrf()
      return apiRequest<CurrentUser>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(values),
      })
    },
    onSuccess: (user) => queryClient.setQueryData(AUTH_QUERY_KEY, user),
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (values: RegisterValues) => {
      await ensureCsrf()
      return apiRequest<CurrentUser>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(values),
      })
    },
    onSuccess: (user) => queryClient.setQueryData(AUTH_QUERY_KEY, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await ensureCsrf()
      await apiRequest<void>('/auth/logout', { method: 'POST', body: '{}' })
    },
    onSuccess: () => {
      queryClient.setQueryData(AUTH_QUERY_KEY, null)
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'auth' })
    },
  })
}
