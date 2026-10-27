const BASE = import.meta.env.VITE_CALC_API ?? '/api/v1'

type ApiErrorBody = {
  detail?: string
  errors?: Record<string, string[] | string>
}

type RequestOptions = {
  suppressUnauthorizedEvent?: boolean
}

function readCookie(name: string) {
  const prefix = `${name}=`
  const part = document.cookie.split('; ').find((item) => item.startsWith(prefix))
  return part ? decodeURIComponent(part.slice(prefix.length)) : ''
}

function normalizeErrors(errors: ApiErrorBody['errors']) {
  if (!errors) return {}
  return Object.fromEntries(
    Object.entries(errors).map(([field, messages]) => [
      field,
      Array.isArray(messages) ? messages : [messages],
    ]),
  )
}

export class ApiError extends Error {
  status: number
  detail: string
  errors: Record<string, string[]>

  constructor(status: number, body: ApiErrorBody = {}) {
    const detail = body.detail ?? `请求失败 (${status})`
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.errors = normalizeErrors(body.errors)
  }
}

export async function apiFetchRaw(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
) {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', readCookie('csrftoken'))
  }
  if (init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })
  if (response.status === 401 && !options.suppressUnauthorizedEvent) {
    window.dispatchEvent(new Event('calc:unauthorized'))
  }
  return response
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
) {
  const response = await apiFetchRaw(path, init, options)
  if (!response.ok) {
    const body = (await response.json().catch(() => ({
      detail: response.statusText || `请求失败 (${response.status})`,
    }))) as ApiErrorBody
    throw new ApiError(response.status, body)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function ensureCsrf() {
  await apiFetchRaw('/auth/csrf')
}
