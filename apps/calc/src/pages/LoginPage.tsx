import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, LoaderCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import { type LoginValues, useLogin } from '../api/auth'
import { ApiError } from '../api/client'
import { safeNextPath } from '../auth/AuthGate'
import { EMPTY_LOGIN_VALUES, resolveLoginDefaults } from '../auth/dev-login'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { AuthLayout } from './AuthLayout'

const loginSchema = z.object({
  email: z.string().trim().min(1, '请输入邮箱').email('请输入有效邮箱'),
  password: z.string().min(1, '请输入密码'),
})

export function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const login = useLogin()
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: import.meta.env.DEV
      ? resolveLoginDefaults({
          dev: true,
          email: import.meta.env.VITE_DEV_LOGIN_EMAIL,
          password: import.meta.env.VITE_DEV_LOGIN_PASSWORD,
        })
      : EMPTY_LOGIN_VALUES,
  })

  async function submit(values: LoginValues) {
    try {
      await login.mutateAsync(values)
      navigate(safeNextPath(searchParams.get('next')), { replace: true })
    } catch (error) {
      if (error instanceof ApiError) {
        for (const field of ['email', 'password'] as const) {
          const message = error.errors[field]?.[0]
          if (message) form.setError(field, { message })
        }
      }
      form.setError('root.server', {
        message: error instanceof ApiError ? error.detail : '登录失败，请稍后重试',
      })
    }
  }

  return (
    <AuthLayout mode="login" title="欢迎回来" description="登录后继续管理项目、方案和计算记录。">
      <form className="space-y-5" onSubmit={form.handleSubmit(submit)} noValidate>
        {form.formState.errors.root?.server?.message && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertDescription>{form.formState.errors.root.server.message}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="login-email">邮箱</Label>
          <Input
            id="login-email"
            type="email"
            autoComplete="email"
            placeholder="name@example.com"
            aria-invalid={Boolean(form.formState.errors.email)}
            aria-describedby={form.formState.errors.email ? 'login-email-error' : undefined}
            {...form.register('email')}
          />
          {form.formState.errors.email && (
            <p id="login-email-error" className="text-xs text-destructive">
              {form.formState.errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="login-password">密码</Label>
          <Input
            id="login-password"
            type="password"
            autoComplete="current-password"
            aria-invalid={Boolean(form.formState.errors.password)}
            aria-describedby={form.formState.errors.password ? 'login-password-error' : undefined}
            {...form.register('password')}
          />
          {form.formState.errors.password && (
            <p id="login-password-error" className="text-xs text-destructive">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>

        <Button
          type="submit"
          size="lg"
          disabled={login.isPending}
          aria-busy={login.isPending}
          className="h-10 w-full bg-[#176b55] text-white hover:bg-[#125744]"
        >
          {login.isPending && <LoaderCircle className="animate-spin" />}
          {login.isPending ? '正在登录…' : '登录'}
        </Button>

        <p className="text-center text-sm text-[#71717a]">
          还没有账号？
          <Link className="ml-1 font-medium text-[#176b55] hover:underline" to="/register">
            创建账号
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
