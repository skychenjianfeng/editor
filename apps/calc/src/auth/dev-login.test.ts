import { describe, expect, it } from 'vitest'
import { EMPTY_LOGIN_VALUES, resolveLoginDefaults } from './dev-login'

describe('resolveLoginDefaults', () => {
  it('prefills complete local development credentials', () => {
    expect(
      resolveLoginDefaults({
        dev: true,
        email: ' demo@example.test ',
        password: 'local-password',
      }),
    ).toEqual({ email: 'demo@example.test', password: 'local-password' })
  })

  it('never exposes credentials in production', () => {
    expect(
      resolveLoginDefaults({
        dev: false,
        email: 'demo@example.test',
        password: 'local-password',
      }),
    ).toEqual(EMPTY_LOGIN_VALUES)
  })

  it('keeps the form empty when either credential is missing', () => {
    expect(resolveLoginDefaults({ dev: true, email: 'demo@example.test', password: '' })).toEqual(
      EMPTY_LOGIN_VALUES,
    )
  })
})
