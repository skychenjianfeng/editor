import { describe, expect, it } from 'vitest'
import { BRAND_MARK, BRAND_NAME } from './branding'

describe('branding', () => {
  it('uses the approved product identity', () => {
    expect(BRAND_NAME).toBe('玄构天枢')
    expect(BRAND_MARK).toBe('玄')
  })
})
