import { describe, expect, test } from 'bun:test'
import { existsSync, statSync } from 'node:fs'
import { join } from 'node:path'

const publicDir = join(import.meta.dir, '../../public')

describe('IFC runtime assets', () => {
  test('copies every WebIFC binary into the editor public directory', () => {
    for (const name of ['web-ifc.wasm', 'web-ifc-mt.wasm', 'web-ifc-node.wasm']) {
      const path = join(publicDir, name)
      expect(existsSync(path)).toBe(true)
      expect(statSync(path).size).toBeGreaterThan(0)
    }
  })
})
