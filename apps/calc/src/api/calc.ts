import { useMutation, useQuery } from '@tanstack/react-query'

import { apiFetchRaw, apiRequest } from './client'
import type { ProjectRecord } from './projects'

const BASE = ''

export type ApiResultItem = {
  no: number
  key: string
  item: string
  value: number
  limit: number
  unit: string
  ratio: number
  ok: boolean
  clause: string
  control: boolean
  detail: string
}

export type RunPayload = {
  run_id: string
  module: string
  verified: boolean
  standard: string
  params: Record<string, unknown>
  summary: { total: number; failed: number; control_failed: number }
  results: ApiResultItem[]
  derived: Record<string, number>
  assumptions: string[]
  standards?: {
    applied: { code: string; name: string }[]
    missing: { code: string; name: string }[]
    complete: boolean
    gaps?: string[]
  }
}

export type RunRecord = {
  run_id: string
  created_at: string
  module: string
  title: string
  standard: string
  verified: boolean
  summary: { total: number; failed: number; control_failed: number }
  total: number
  failed: number
  control_failed: number
}

export type { ProjectRecord } from './projects'

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

export type ParamField = {
  key: string
  label: string
  type: 'number' | 'select' | 'boolean'
  unit?: string
  default?: unknown
  step?: number
  options?: string[]
  limit?: string
}

export type ParamGroup = {
  key?: string
  title: string
  fields: ParamField[]
}

export type ParamSpec = {
  module: string
  title: string
  standard: string
  verified: boolean
  groups: ParamGroup[]
}

export type GeometryItem =
  | { type: 'line'; x1: number; y1: number; x2: number; y2: number }
  | { type: 'circle'; x: number; y: number; r: number }
  | { type: 'text'; text: string; x: number; y: number; size: number; rotation: number }

export type GeometryLayer = { id: string; name: string; color: string; items: GeometryItem[] }

export type View = 'elevation' | 'plan' | 'side' | 'section'

export type GeometryPayload = {
  view: View
  units: string
  bounds: { minX: number; minY: number; maxX: number; maxY: number }
  layers: GeometryLayer[]
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  return apiRequest<T>(url, init)
}

export function useParamSpec(module = 'scaffold-fastener') {
  return useQuery({
    queryKey: ['param-spec', module],
    queryFn: () => getJson<ParamSpec>(`${BASE}/catalog/param-spec/${module}`),
    staleTime: 5 * 60 * 1000,
  })
}

export type ModuleInfo = {
  key: string
  title: string
  standard: string
  verified: boolean
  available: boolean
  status: 'available' | 'planned'
  note: string
  category?: string
}

export type ModuleCategory = {
  key: string
  title: string
  isNew: boolean
  modules: ModuleInfo[]
}

export type ModuleCatalog = {
  regions: string[]
  categories: ModuleCategory[]
  modules: ModuleInfo[]
}

export function useModules() {
  return useQuery({
    queryKey: ['modules'],
    queryFn: () => getJson<ModuleCatalog>(`${BASE}/catalog/modules`),
    staleTime: 10 * 60 * 1000,
  })
}

export function useRunCalc(module = 'scaffold-fastener') {
  return useMutation({
    mutationFn: (params: Record<string, unknown>) =>
      getJson<RunPayload>(`${BASE}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module, params }),
      }),
  })
}

export async function fetchRunDetail(runId: string) {
  return getJson<RunPayload>(`${BASE}/runs/${encodeURIComponent(runId)}`)
}

export function useRuns(limit = 50) {
  return useQuery({
    queryKey: ['runs', limit],
    queryFn: () => getJson<{ runs: RunRecord[] }>(`${BASE}/runs?limit=${limit}`),
    staleTime: 10 * 1000,
  })
}

export async function fetchProjects(search = '', limit = 200) {
  const query = new URLSearchParams({ limit: String(limit) })
  if (search.trim()) query.set('search', search.trim())
  return getJson<{ projects: ProjectRecord[] }>(`${BASE}/projects?${query}`)
}

export async function createProject(payload: {
  name: string
  code?: string
  client?: string
  location?: string
  designer?: string
  note?: string
}) {
  return getJson<ProjectRecord>(`${BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateProject(
  projectId: string,
  payload: Partial<
    Pick<ProjectRecord, 'name' | 'code' | 'client' | 'location' | 'designer' | 'note'>
  >,
) {
  return getJson<ProjectRecord>(`${BASE}/projects/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteProject(projectId: string) {
  await apiRequest<void>(`${BASE}/projects/${projectId}`, { method: 'DELETE' })
}

export async function fetchSchemes(projectId: string) {
  return getJson<{ schemes: SchemeRecord[] }>(`${BASE}/projects/${projectId}/schemes`)
}

export async function createScheme(
  projectId: string,
  payload: {
    name: string
    module: string
    params: Record<string, unknown>
    last_run_id?: string | null
  },
) {
  return getJson<SchemeRecord>(`${BASE}/projects/${projectId}/schemes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateScheme(
  schemeId: string,
  payload: Partial<Pick<SchemeRecord, 'name' | 'module' | 'params'>> & {
    last_run_id?: string | null
  },
) {
  return getJson<SchemeRecord>(`${BASE}/schemes/${schemeId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteScheme(schemeId: string) {
  await apiRequest<void>(`${BASE}/schemes/${schemeId}`, { method: 'DELETE' })
}

export function useGeometry(
  params: Record<string, unknown>,
  view: View,
  module = 'scaffold-fastener',
) {
  return useQuery({
    queryKey: ['geometry', module, view, params],
    queryFn: () =>
      getJson<GeometryPayload>(`${BASE}/geometry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module, params, view }),
      }),
    staleTime: 60 * 1000,
  })
}

export async function downloadReport(
  params: Record<string, unknown>,
  module = 'scaffold-fastener',
  moduleTitle?: string,
) {
  const res = await apiFetchRaw(`${BASE}/report.docx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module, params }),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${moduleTitle ?? '脚手架'}计算书.docx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function downloadDrawing(
  kind: 'dxf' | 'png',
  params: Record<string, unknown>,
  view: View,
  module = 'scaffold-fastener',
  moduleTitle?: string,
) {
  const res = await apiFetchRaw(`${BASE}/export.${kind}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module, params, view }),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const viewLabel = { elevation: '立面', plan: '平面', side: '侧面', section: '剖面' }[view]
  a.download = `${moduleTitle ?? '脚手架'}-${viewLabel}.${kind}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export type BatchRow = {
  index: number
  name: string
  params: Record<string, unknown>
  module: string
  primary_item: string | null
  primary_key: string | null
  primary_value: number | null
  primary_unit: string | null
  primary_ratio: number | null
  primary_ok: boolean | null
  failed: number
  control_failed: number
  ok: boolean
  h?: number | null
  la?: number | null
  lb?: number | null
  H?: number | null
  upright?: number | null
  upright_ratio?: number | null
  lambda?: number | null
}

export type BatchResult = {
  count: number
  failed: number
  control_failed: number
  rows: BatchRow[]
}

export function useBatch(module = 'scaffold-fastener') {
  return useMutation({
    mutationFn: (cases: Record<string, unknown>[]) =>
      getJson<BatchResult>(`${BASE}/batches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module, cases }),
      }),
  })
}

export async function downloadBatchCsv(
  cases: Record<string, unknown>[],
  module = 'scaffold-fastener',
) {
  const res = await apiFetchRaw(`${BASE}/export.batch.csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module, cases }),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '批量工况结果.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function downloadResultsCsv(
  params: Record<string, unknown>,
  module = 'scaffold-fastener',
  moduleTitle?: string,
) {
  const res = await apiFetchRaw(`${BASE}/export.results.csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module, params }),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${moduleTitle ?? '脚手架'}-计算结果.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
