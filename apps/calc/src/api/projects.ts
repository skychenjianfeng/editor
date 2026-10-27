import { useQuery } from '@tanstack/react-query'
import { apiRequest, ensureCsrf } from './client'

export const REGIONS = [
  '全国',
  '上海',
  '江苏',
  '浙江',
  '北京',
  '山东',
  '广东',
  '湖北',
  '福建',
  '重庆',
] as const

export const PROJECT_STATUSES = [
  { value: 'preparing', label: '筹备中' },
  { value: 'calculating', label: '计算中' },
  { value: 'completed', label: '已完成' },
] as const

export type ProjectStatus = (typeof PROJECT_STATUSES)[number]['value']
export type ProjectRegion = (typeof REGIONS)[number]

export type SchemeRecord = {
  scheme_id: string
  project_id: string
  name: string
  module: string
  module_title: string
  params: Record<string, unknown>
  last_run_id: string | null
  created_at: string
  updated_at: string
}

export type ProjectRecord = {
  project_id: string
  name: string
  region: ProjectRegion
  status: ProjectStatus
  status_label: string
  scheme_count: number
  failed_control_count: number
  last_calculated_at: string | null
  code: string
  client: string
  location: string
  designer: string
  note: string
  created_at: string
  updated_at: string
  schemes?: SchemeRecord[]
}

export type ProjectFormValues = {
  name: string
  region: ProjectRegion
  status: ProjectStatus
  code: string
  client: string
  location: string
  designer: string
  note: string
}

export type ProjectFilters = {
  search: string
  status?: ProjectStatus
}

function projectQuery(filters: ProjectFilters) {
  const query = new URLSearchParams({ limit: '200' })
  if (filters.search.trim()) query.set('search', filters.search.trim())
  if (filters.status) query.set('status', filters.status)
  return query.toString()
}

export function useProjects(filters: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => apiRequest<{ projects: ProjectRecord[] }>(`/projects?${projectQuery(filters)}`),
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => apiRequest<ProjectRecord>(`/projects/${encodeURIComponent(projectId!)}`),
    enabled: Boolean(projectId),
  })
}

export async function createProject(values: ProjectFormValues) {
  await ensureCsrf()
  return apiRequest<ProjectRecord>('/projects', {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export async function updateProject(projectId: string, values: ProjectFormValues) {
  await ensureCsrf()
  return apiRequest<ProjectRecord>(`/projects/${encodeURIComponent(projectId)}`, {
    method: 'PATCH',
    body: JSON.stringify(values),
  })
}

export async function deleteProject(projectId: string) {
  await ensureCsrf()
  return apiRequest<void>(`/projects/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  })
}
