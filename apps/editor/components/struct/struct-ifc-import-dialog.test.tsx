import { afterEach, beforeEach, describe, expect, test } from 'bun:test'
import type { SceneGraph } from '@pascal-app/editor'
import type { ReactElement } from 'react'
import { act, create, type ReactTestInstance, type ReactTestRenderer } from 'react-test-renderer'
import {
  IfcImportDialogView,
  type IfcImportViewState,
  isIfcFileName,
  validateIfcConversionGraph,
} from './struct-ifc-import-dialog'

const originalActEnvironment = (
  globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT

let renderers: ReactTestRenderer[] = []

function mount(element: ReactElement): ReactTestRenderer {
  let renderer: ReactTestRenderer | null = null
  act(() => {
    renderer = create(element)
  })
  if (!renderer) throw new Error('renderer did not mount')
  renderers.push(renderer)
  return renderer
}

function render(state: IfcImportViewState) {
  return mount(
    <IfcImportDialogView
      onCancel={() => {}}
      onChooseFile={() => {}}
      onConfirm={() => {}}
      onDropFile={() => {}}
      onProjectNameChange={() => {}}
      onRetry={() => {}}
      state={state}
    />,
  )
}

function byTestId(renderer: ReactTestRenderer, testId: string): ReactTestInstance {
  return renderer.root.findByProps({ 'data-testid': testId })
}

function text(renderer: ReactTestRenderer): string {
  return JSON.stringify(renderer.toJSON())
}

beforeEach(() => {
  ;(
    globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }
  ).IS_REACT_ACT_ENVIRONMENT = true
})

afterEach(() => {
  for (const renderer of renderers) act(() => renderer.unmount())
  renderers = []
  ;(
    globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }
  ).IS_REACT_ACT_ENVIRONMENT = originalActEnvironment
})

describe('IFC conversion result validation', () => {
  test('rejects an empty graph', () => {
    expect(validateIfcConversionGraph({ nodes: {}, rootNodeIds: [] })).toMatchObject({
      ok: false,
      reason: 'empty',
    })
  })

  test('rejects hierarchy without renderable geometry', () => {
    const graph = {
      nodes: {
        site_1: { id: 'site_1', type: 'site', children: ['level_1'] },
        level_1: { id: 'level_1', type: 'level', parentId: 'site_1', children: ['imesh_1'] },
        imesh_1: {
          id: 'imesh_1',
          type: 'imported-mesh',
          parentId: 'level_1',
          primitives: [],
        },
      },
      rootNodeIds: ['site_1'],
    } as unknown as SceneGraph

    expect(validateIfcConversionGraph(graph)).toMatchObject({
      ok: false,
      reason: 'no-renderable-geometry',
    })
  })

  test('accepts a graph containing renderable geometry', () => {
    const graph = {
      nodes: {
        wall_1: {
          id: 'wall_1',
          type: 'wall',
          start: [0, 0],
          end: [4, 0],
          thickness: 0.2,
          height: 3,
          children: [],
        },
      },
      rootNodeIds: ['wall_1'],
    } as unknown as SceneGraph

    expect(validateIfcConversionGraph(graph)).toMatchObject({
      ok: true,
      renderableNodeCount: 1,
    })
  })

  test('accepts the converter block topology used for beams', () => {
    const graph = {
      nodes: {
        block_1: {
          id: 'block_1',
          type: 'block',
          topology: {
            vertices: [
              { id: 'v0', position: [0, 0, 0] },
              { id: 'v1', position: [1, 0, 0] },
              { id: 'v2', position: [0, 1, 0] },
            ],
            edges: [
              { id: 'e0', vertexIds: ['v0', 'v1'] },
              { id: 'e1', vertexIds: ['v1', 'v2'] },
              { id: 'e2', vertexIds: ['v2', 'v0'] },
            ],
            faces: [{ id: 'f0', vertexIds: ['v0', 'v1', 'v2'], materialSlot: 'body' }],
          },
          children: [],
        },
      },
      rootNodeIds: ['block_1'],
    } as unknown as SceneGraph

    expect(validateIfcConversionGraph(graph)).toMatchObject({
      ok: true,
      renderableNodeCount: 1,
    })
  })

  test('matches only the IFC extension case-insensitively', () => {
    expect(isIfcFileName('House.IFC')).toBe(true)
    expect(isIfcFileName('house.ifc')).toBe(true)
    expect(isIfcFileName('house.ifczip')).toBe(false)
    expect(isIfcFileName('house.txt')).toBe(false)
  })
})

describe('IFC import dialog view', () => {
  test('offers only IFC files when idle', () => {
    const renderer = render({ phase: 'idle' })
    const dialog = renderer.root.findByProps({ role: 'dialog' })
    const input = renderer.root.findByType('input')

    expect(dialog.props['aria-modal']).toBe('true')
    expect(input.props.accept).toContain('.ifc')
    expect(input.props.className).toContain('hidden')
    expect(text(renderer)).toContain('选择 IFC 文件')
    expect(text(renderer)).toContain('第一阶段不参与结构统计和 analysis-model')
  })

  test('shows the selected file and conversion percentage', () => {
    const renderer = render({
      phase: 'converting',
      fileName: 'house.ifc',
      message: 'Processing walls...',
      percent: 60,
    })

    expect(text(renderer)).toContain('house.ifc')
    expect(text(renderer)).toContain('60%')
    expect(text(renderer)).toContain('Processing walls')
    expect(byTestId(renderer, 'ifc-import-progress').props['aria-valuenow']).toBe(60)
  })

  test('shows review counts and enables creating a project', () => {
    const renderer = render({
      phase: 'review',
      fileName: 'house.ifc',
      projectName: 'House',
      summary: {
        nodeCount: 12,
        levelCount: 2,
        importedMeshCount: 3,
        typeCounts: { wall: 4, slab: 2 },
        sourceFile: 'house.ifc',
      },
    })
    const createButton = byTestId(renderer, 'ifc-import-create')

    expect(text(renderer)).toContain('12')
    expect(text(renderer)).toContain('2 层')
    expect(text(renderer)).toContain('3')
    expect(text(renderer)).toContain('wall')
    expect(createButton.props.disabled).toBe(false)
    expect(text(renderer)).toContain('第一阶段不参与结构统计和 analysis-model')
  })

  test('announces an error and offers retry', () => {
    const renderer = render({
      phase: 'error',
      fileName: 'broken.ifc',
      message: '无法读取 IFC',
    })

    expect(renderer.root.findByProps({ role: 'alert' }).props.children).toContain('无法读取 IFC')
    expect(byTestId(renderer, 'ifc-import-retry').props.disabled).toBe(false)
    expect(text(renderer)).toContain('第一阶段不参与结构统计和 analysis-model')
  })

  test('blocks file and cancellation replacements while creating', () => {
    const renderer = render({
      phase: 'creating',
      fileName: 'house.ifc',
      projectName: 'House',
      summary: {
        nodeCount: 12,
        levelCount: 2,
        importedMeshCount: 3,
        typeCounts: { wall: 4, slab: 2 },
        sourceFile: 'house.ifc',
      },
    })

    expect(renderer.root.findByProps({ type: 'file' }).props.disabled).toBe(true)
    expect(byTestId(renderer, 'ifc-import-reselect').props.disabled).toBe(true)
    expect(byTestId(renderer, 'ifc-import-cancel').props.disabled).toBe(true)
    expect(byTestId(renderer, 'ifc-import-create').props.disabled).toBe(true)
  })
})
