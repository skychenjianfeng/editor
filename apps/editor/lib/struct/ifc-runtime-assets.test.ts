import { describe, expect, test } from 'bun:test'
import { spawnSync } from 'node:child_process'
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const publicDir = join(import.meta.dir, '../../public')
const sourceScript = join(import.meta.dir, '../../scripts/copy-web-ifc-wasm.mjs')

function createFixture() {
  const root = mkdtempSync(join(tmpdir(), 'editor-ifc-assets-'))
  const scriptsDir = join(root, 'scripts')
  mkdirSync(scriptsDir)
  const script = join(scriptsDir, 'copy-web-ifc-wasm.mjs')
  copyFileSync(sourceScript, script)
  return { root, script }
}

function runFixture(script: string, cwd: string) {
  return spawnSync(process.execPath, [script], {
    cwd,
    encoding: 'utf8',
    timeout: 2_000,
  })
}

describe('IFC runtime assets', () => {
  test('copies every WebIFC binary into the editor public directory', () => {
    for (const name of ['web-ifc.wasm', 'web-ifc-mt.wasm', 'web-ifc-node.wasm']) {
      const path = join(publicDir, name)
      expect(existsSync(path)).toBe(true)
      expect(statSync(path).size).toBeGreaterThan(0)
    }
  })

  test('copies binaries from an isolated installed package', () => {
    const { root, script } = createFixture()
    try {
      const packageDir = join(root, 'node_modules', 'web-ifc')
      mkdirSync(packageDir, { recursive: true })
      const contents = new Map([
        ['web-ifc.wasm', 'main-wasm'],
        ['web-ifc-mt.wasm', 'threaded-wasm'],
        ['web-ifc-node.wasm', 'node-wasm'],
      ])
      for (const [name, content] of contents) {
        writeFileSync(join(packageDir, name), content)
      }

      const result = runFixture(script, root)

      expect(result.status).toBe(0)
      expect(result.stderr).toBe('')
      for (const [name, content] of contents) {
        expect(readFileSync(join(root, 'public', name), 'utf8')).toBe(content)
        expect(result.stdout).toContain(`[editor:ifc] copied ${name}`)
      }
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  test('exits non-zero promptly when web-ifc is missing', () => {
    const { root, script } = createFixture()
    try {
      const result = runFixture(script, root)

      expect(result.error).toBeUndefined()
      expect(result.status).toBe(1)
      expect(result.stderr).toContain('[editor:ifc] web-ifc package not found')
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
