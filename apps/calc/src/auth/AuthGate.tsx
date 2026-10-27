import { useQueryClient } from '@tanstack/react-query'
import { AlertCircle, LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useCurrentUser } from '../api/auth'
import { ApiError } from '../api/client'
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert'
import { Button } from '../components/ui/button'
import { Skeleton } from '../components/ui/skeleton'

export function safeNextPath(value: string | null) {
  return value?.startsWith('/') && !value.startsWith('//') ? value : '/workspace'
}

function loginPath(location: ReturnType<typeof useLocation>) {
  const next = `${location.pathname}${location.search}`
  return `/login?next=${encodeURIComponent(next)}`
}

export function AuthGate() {
  const location = useLocation()
  const queryClient = useQueryClient()
  const currentUser = useCurrentUser()
  const [unauthorized, setUnauthorized] = useState(false)

  useEffect(() => {
    function handleUnauthorized() {
      setUnauthorized(true)
      queryClient.removeQueries()
    }

    window.addEventListener('calc:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('calc:unauthorized', handleUnauthorized)
  }, [queryClient])

  if (unauthorized) return <Navigate to={loginPath(location)} replace />

  if (currentUser.isPending) {
    return (
      <main
        role="status"
        aria-live="polite"
        className="grid min-h-screen place-items-center bg-[#f7f7f8] p-6"
      >
        <div className="w-full max-w-sm space-y-4 rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-[#3f3f46]">
            <LoaderCircle className="size-4 animate-spin text-[#176b55]" />
            正在恢复会话
          </div>
          <Skeleton className="h-8 w-3/5" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </main>
    )
  }

  if (currentUser.isError) {
    if (currentUser.error instanceof ApiError && currentUser.error.status === 401) {
      return <Navigate to={loginPath(location)} replace />
    }
    return (
      <main className="grid min-h-screen place-items-center bg-[#f7f7f8] p-6">
        <Alert variant="destructive" className="max-w-lg bg-white">
          <AlertCircle />
          <AlertTitle>无法恢复登录状态</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>请检查网络连接后重试。</p>
            <Button variant="outline" size="sm" onClick={() => void currentUser.refetch()}>
              重试
            </Button>
          </AlertDescription>
        </Alert>
      </main>
    )
  }

  return <Outlet />
}
