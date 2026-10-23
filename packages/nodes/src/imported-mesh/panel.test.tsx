import { afterEach, beforeEach, describe, expect, test } from 'bun:test'
import { ImportedMeshNode, useScene } from '@pascal-app/core'
import { createEditorApi, getMovingNode, useInteractionScope } from '@pascal-app/editor'
import { useViewer } from '@pascal-app/viewer'
import type { ReactElement } from 'react'
import { act, create, type ReactTestRenderer } from 'react-test-renderer'
import { ImportedMeshPanelBody } from './panel'

globalThis.requestAnimationFrame ??= (() => 0) as typeof requestAnimationFrame
globalThis.cancelAnimationFrame ??= (() => {}) as typeof cancelAnimationFrame

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

function text(renderer: ReactTestRenderer): string {
  return JSON.stringify(renderer.toJSON())
}

function instanceText(instance: ReturnType<ReactTestRenderer['root']['findByType']>): string {
  return instance.children
    .map((child) => (typeof child === 'string' ? child : instanceText(child)))
    .join('')
}

function seedNode(node: ImportedMeshNode, readOnly = false) {
  useScene.setState({
    dirtyNodes: new Set(),
    nodes: { [node.id]: node },
    readOnly,
    rootNodeIds: [node.id],
  } as never)
}

function realActions(node: ImportedMeshNode, readOnly = false) {
  return {
    onDelete: () => {
      useScene.getState().deleteNode(node.id)
      useViewer.getState().setSelection({ selectedIds: [] })
    },
    onMove: () => {
      createEditorApi().engageMove(node)
      useViewer.getState().setSelection({ selectedIds: [] })
    },
    onUpdate: (patch: Partial<ImportedMeshNode>) => useScene.getState().updateNode(node.id, patch),
    readOnly,
  }
}

function findButton(renderer: ReactTestRenderer, label: string) {
  const button = renderer.root
    .findAllByType('button')
    .find((instance) => instanceText(instance).trim() === label)
  if (!button) throw new Error(`button ${label} did not render`)
  return button
}

beforeEach(() => {
  ;(
    globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }
  ).IS_REACT_ACT_ENVIRONMENT = true
  seedNode(
    ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      name: 'Imported Beam',
      metadata: {
        ifcType: 'IFCBEAM',
        globalId: '0YvctVUKr0kugbFTf53O9L',
        expressID: 42,
        typeName: 'Beam Type',
        material: 'Steel',
      },
    }),
  )
})

afterEach(() => {
  for (const renderer of renderers) act(() => renderer.unmount())
  renderers = []
  useScene.setState({
    dirtyNodes: new Set(),
    nodes: {},
    readOnly: false,
    rootNodeIds: [],
  } as never)
  useViewer.getState().setSelection({ selectedIds: [] })
  useInteractionScope.getState().end()
  ;(
    globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT?: boolean }
  ).IS_REACT_ACT_ENVIRONMENT = originalActEnvironment
})

describe('imported IFC mesh panel', () => {
  test('shows IFC metadata as read-only source facts', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      name: 'Imported Beam',
      metadata: {
        ifcType: 'IFCBEAM',
        globalId: '0YvctVUKr0kugbFTf53O9L',
        expressID: 42,
        typeName: 'Beam Type',
        material: 'Steel',
      },
    })
    seedNode(node)
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node)} />)
    const renderedText = text(renderer)
    const metadata = renderer.root.findByProps({ 'data-testid': 'imported-mesh-metadata' })

    expect(renderedText).toContain('IFC 导入实体')
    expect(renderedText).toContain('IFCBEAM')
    expect(renderedText).toContain('GlobalId')
    expect(renderedText).toContain('ExpressID')
    expect(renderedText).toContain('来源类型')
    expect(renderedText).toContain('Beam Type')
    expect(renderedText).toContain('材料')
    expect(renderedText).toContain('Steel')
    expect(renderedText).toContain('几何按 IFC 保留；截面和结构计算参数暂不可编辑。')
    expect(metadata.findAllByType('input')).toHaveLength(0)
    expect(metadata.findAllByType('select')).toHaveLength(0)
    expect(metadata.findAllByType('textarea')).toHaveLength(0)
  })

  test('edits the node name through the real scene update API', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      name: 'Imported Beam',
      metadata: { ifcType: 'IFCBEAM' },
    })
    seedNode(node)
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node)} />)
    const input = renderer.root.findByType('input')

    expect(input.props.value).toBe('Imported Beam')
    act(() => input.props.onChange({ currentTarget: { value: 'Renamed Beam' } }))

    expect(useScene.getState().nodes[node.id]?.name).toBe('Renamed Beam')
  })

  test('toggles node visibility through the real scene update API', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      metadata: { ifcType: 'IFCBEAM' },
    })
    seedNode(node)
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node)} />)

    act(() => findButton(renderer, '隐藏').props.onClick())

    expect(useScene.getState().nodes[node.id]?.visible).toBe(false)
  })

  test('deletes the node and clears the selection through real scene and viewer APIs', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      metadata: { ifcType: 'IFCBEAM' },
    })
    seedNode(node)
    useViewer.getState().setSelection({ selectedIds: [node.id] })
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node)} />)

    act(() => findButton(renderer, '删除').props.onClick())

    expect(useScene.getState().nodes[node.id]).toBeUndefined()
    expect(useViewer.getState().selection.selectedIds).toEqual([])
  })

  test('engages the real move tool and clears the selection', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      metadata: { ifcType: 'IFCBEAM' },
    })
    seedNode(node)
    useViewer.getState().setSelection({ selectedIds: [node.id] })
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node)} />)

    act(() => findButton(renderer, '移动').props.onClick())

    expect(getMovingNode()?.id).toBe(node.id)
    expect(useViewer.getState().selection.selectedIds).toEqual([])
  })

  test('disables the name editor when the scene is read-only', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_ifc_beam',
      name: 'Imported Beam',
      metadata: { ifcType: 'IFCBEAM' },
    })
    seedNode(node, true)
    const renderer = mount(<ImportedMeshPanelBody node={node} {...realActions(node, true)} />)

    expect(renderer.root.findByType('input').props.disabled).toBe(true)
  })
})
