import type { LoginValues } from '../api/auth'

export type DevLoginInput = {
  dev: boolean
  email?: string
  password?: string
}

export const EMPTY_LOGIN_VALUES: LoginValues = { email: '', password: '' }

export function resolveLoginDefaults(input: DevLoginInput): LoginValues {
  if (!input.dev) return EMPTY_LOGIN_VALUES
  const email = input.email?.trim() ?? ''
  const password = input.password ?? ''
  if (!email || !password) return EMPTY_LOGIN_VALUES
  return { email, password }
}
