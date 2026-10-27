import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProjectFormDialog } from './ProjectFormDialog'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  document.cookie = 'csrftoken=; Max-Age=0; Path=/'
})

function renderDialog(onCreated = vi.fn()) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <ProjectFormDialog open onOpenChange={vi.fn()} onCreated={onCreated} />
    </QueryClientProvider>,
  )
  return { onCreated }
}

describe('ProjectFormDialog', () => {
  it('defaults to 全国 and blocks an empty project name', async () => {
    const fetchMock = vi.fn(async () => new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    renderDialog()

    expect(screen.getByLabelText('项目地区')).toHaveValue('全国')
    fireEvent.click(screen.getByRole('button', { name: '创建并进入' }))
    expect(await screen.findByText('项目名称必填')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('submits the selected region and enters the new project', async () => {
    document.cookie = 'csrftoken=project-token; Path=/'
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      if (String(input).endsWith('/auth/csrf')) return new Response('{}', { status: 200 })
      return new Response(
        JSON.stringify({
          project_id: '11111111-1111-4111-8111-111111111111',
          name: '滨江研发楼改造',
          region: '上海',
          status: 'preparing',
          status_label: '筹备中',
          scheme_count: 0,
          failed_control_count: 0,
          last_calculated_at: null,
          code: '',
          client: '',
          location: '',
          designer: '',
          note: '',
          created_at: '2026-10-27T00:00:00Z',
          updated_at: '2026-10-27T00:00:00Z',
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    const { onCreated } = renderDialog()
    fireEvent.change(screen.getByLabelText('项目名称'), {
      target: { value: '滨江研发楼改造' },
    })
    fireEvent.change(screen.getByLabelText('项目地区'), { target: { value: '上海' } })
    fireEvent.click(screen.getByRole('button', { name: '创建并进入' }))

    await waitFor(() => expect(onCreated).toHaveBeenCalled())
    const post = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/projects') && init?.method === 'POST',
    ) as [RequestInfo | URL, RequestInit] | undefined
    expect(post).toBeDefined()
    expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({
      name: '滨江研发楼改造',
      region: '上海',
      status: 'preparing',
    })
    expect(new Headers(post?.[1]?.headers).get('X-CSRFToken')).toBe('project-token')
    expect(onCreated).toHaveBeenCalledWith(expect.objectContaining({ region: '上海' }), 'enter')
  })
})
