import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, LoaderCircle } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import { type RegisterValues, useRegister } from '../api/auth'
import { ApiError } from '../api/client'
import { safeNextPath } from '../auth/AuthGate'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { AuthLayout } from './AuthLayout'

const registerSchema = z
  .object({
    email: z.string().trim().min(1, '请输入邮箱').email('请输入有效邮箱'),
    password: z.string().min(8, '密码至少需要 8 个字符'),
    password_confirm: z.string().min(1, '请再次输入密码'),
  })
  .refine((values) => values.password === values.password_confirm, {
    path: ['password_confirm'],
    message: '两次输入的密码不一致',
  })

export function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const registerAccount = useRegister()
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '', password_confirm: '' },
  })

  async function submit(values: RegisterValues) {
    try {
      await registerAccount.mutateAsync(values)
      const next = searchParams.get('next')
      navigate(safeNextPath(next), { replace: true })
    } catch (error) {
      if (error instanceof ApiError) {
        for (const field of ['email', 'password', 'password_confirm'] as const) {
          const message = error.errors[field]?.[0]
          if (message) form.setError(field, { message })
        }
      }
      form.setError('root.server', {
        message: error instanceof ApiError ? error.detail : '注册失败，请稍后重试',
      })
    }
  }

  return (
    <AuthLayout
      mode="register"
      title="创建工程账号"
      description="开放注册。无需邮件验证，注册后将自动登录。"
    >
      <form className="space-y-4" onSubmit={form.handleSubmit(submit)} noValidate>
        {form.formState.errors.root?.server?.message && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertDescription>{form.formState.errors.root.server.message}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="register-email">邮箱</Label>
          <Input
            id="register-email"
            type="email"
            autoComplete="email"
            placeholder="name@example.com"
            aria-invalid={Boolean(form.formState.errors.email)}
            aria-describedby={form.formState.errors.email ? 'register-email-error' : undefined}
            {...form.register('email')}
          />
          {form.formState.errors.email && (
            <p id="register-email-error" className="text-xs text-destructive">
              {form.formState.errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="register-password">密码</Label>
          <Input
            id="register-password"
            type="password"
            autoComplete="new-password"
            aria-invalid={Boolean(form.formState.errors.password)}
            aria-describedby={
              form.formState.errors.password ? 'register-password-error' : undefined
            }
            {...form.register('password')}
          />
          {form.formState.errors.password && (
            <p id="register-password-error" className="text-xs text-destructive">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="register-password-confirm">确认密码</Label>
          <Input
            id="register-password-confirm"
            type="password"
            autoComplete="new-password"
            aria-invalid={Boolean(form.formState.errors.password_confirm)}
            aria-describedby={
              form.formState.errors.password_confirm ? 'register-password-confirm-error' : undefined
            }
            {...form.register('password_confirm')}
          />
          {form.formState.errors.password_confirm && (
            <p id="register-password-confirm-error" className="text-xs text-destructive">
              {form.formState.errors.password_confirm.message}
            </p>
          )}
        </div>

        <Button
          type="submit"
          size="lg"
          disabled={registerAccount.isPending}
          aria-busy={registerAccount.isPending}
          className="h-10 w-full bg-[#176b55] text-white hover:bg-[#125744]"
        >
          {registerAccount.isPending && <LoaderCircle className="animate-spin" />}
          {registerAccount.isPending ? '正在创建账号…' : '注册'}
        </Button>

        <p className="text-center text-sm text-[#71717a]">
          已有账号？
          <Link className="ml-1 font-medium text-[#176b55] hover:underline" to="/login">
            返回登录
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
