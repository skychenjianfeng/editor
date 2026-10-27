import { afterEach, describe, expect, it, vi } from 'vitest'
import { type ApiError, apiRequest } from './client'

afterEach(() => {
  vi.restoreAllMocks()
  document.cookie = 'csrftoken=; Max-Age=0; Path=/'
})

describe('apiRequest', () => {
  it('includes credentials and sends the CSRF cookie on writes', async () => {
    document.cookie = 'csrftoken=csrf-test-token; Path=/'
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify({ name: '项目' }),
    })

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    const headers = new Headers(init.headers)
    expect(url).toBe('/api/v1/projects')
    expect(init.credentials).toBe('include')
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(headers.get('X-CSRFToken')).toBe('csrf-test-token')
  })

  it('preserves backend detail and field errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: '注册信息有误',
              errors: { email: ['该邮箱已注册'] },
            }),
            { status: 400, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    )

    const request = apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({}),
    })

    await expect(request).rejects.toMatchObject({
      status: 400,
      detail: '注册信息有误',
      errors: { email: ['该邮箱已注册'] },
    } satisfies Partial<ApiError>)
  })

  it('emits an authentication failure event for protected requests', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 401 })),
    )
    const listener = vi.fn()
    window.addEventListener('calc:unauthorized', listener)

    await expect(apiRequest('/projects')).rejects.toMatchObject({ status: 401 })

    expect(listener).toHaveBeenCalledTimes(1)
    window.removeEventListener('calc:unauthorized', listener)
  })
})
