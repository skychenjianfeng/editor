import { describe, expect, test } from 'bun:test'
import { BuildingNode, ImportedMeshNode, LevelNode, SiteNode } from '@pascal-app/core'
import type { SceneGraph } from '@pascal-app/editor'
import { normalizeIfcSceneGraph, prepareIfcProjectImport, summarizeIfcGraph } from './ifc-import'

describe('IFC import graph preparation', () => {
  test('wraps building roots in an empty root site', () => {
    const building = BuildingNode.parse({ id: 'building_ifc' })
    const level = LevelNode.parse({ id: 'level_ifc', parentId: building.id, level: 0 })
    const graph = {
      nodes: {
        [building.id]: { ...building, children: [level.id] },
        [level.id]: level,
      },
      rootNodeIds: [building.id],
    } as unknown as SceneGraph

    const normalized = normalizeIfcSceneGraph(graph)
    const site = Object.values(normalized.nodes).find((node) => node.type === 'site')

    expect(site?.type).toBe('site')
    expect(site?.type === 'site' ? site.polygon.points : null).toEqual([])
    expect(site?.children).toContain(building.id)
    expect(normalized.rootNodeIds).toEqual([site?.id])
    expect(normalized.nodes[building.id]?.parentId).toBe(site?.id)
    expect(normalized.nodes[building.id]).not.toBe(graph.nodes[building.id])
    expect(graph.nodes[building.id]?.parentId).toBeNull()
  })

  test('creates a root site container for multiple existing sites', () => {
    const first = SiteNode.parse({ id: 'site_first', polygon: { type: 'polygon', points: [] } })
    const second = SiteNode.parse({ id: 'site_second', polygon: { type: 'polygon', points: [] } })
    const graph = {
      nodes: { [first.id]: first, [second.id]: second },
      rootNodeIds: [first.id, second.id],
    } as unknown as SceneGraph

    const normalized = normalizeIfcSceneGraph(graph)
    const root = normalized.nodes[normalized.rootNodeIds[0]!]

    expect(root?.type).toBe('site')
    expect(root?.children).toEqual([first.id, second.id])
    expect(normalized.nodes[first.id]?.parentId).toBe(root?.id)
    expect(normalized.nodes[second.id]?.parentId).toBe(root?.id)
    expect(graph.nodes[first.id]?.parentId).toBeNull()
    expect(graph.nodes[second.id]?.parentId).toBeNull()
  })

  test('summarizes levels and imported entities', () => {
    const level = LevelNode.parse({ id: 'level_summary', level: 0 })
    const mesh = ImportedMeshNode.parse({
      id: 'imesh_summary',
      parentId: level.id,
      primitives: [],
    })
    const graph = {
      nodes: {
        [level.id]: { ...level, children: [mesh.id] },
        [mesh.id]: mesh,
      },
      rootNodeIds: [level.id],
    } as unknown as SceneGraph

    expect(summarizeIfcGraph(graph, 'model.ifc')).toEqual({
      nodeCount: 2,
      levelCount: 1,
      importedMeshCount: 1,
      typeCounts: { level: 1, 'imported-mesh': 1 },
      sourceFile: 'model.ifc',
    })
  })

  test('adds StructWeb metadata without dropping IFC metadata', () => {
    const site = SiteNode.parse({
      id: 'site_meta',
      polygon: { type: 'polygon', points: [] },
      metadata: { ifcType: 'IFCSITE', globalId: 'guid-site' },
    })
    const input = {
      graph: { nodes: { [site.id]: site }, rootNodeIds: [site.id] } as unknown as SceneGraph,
      projectName: 'Imported House',
      sourceFile: 'house.ifc',
      projectId: 'struct-ifc-house',
      now: new Date('2026-10-23T00:00:00Z'),
    }

    const prepared = prepareIfcProjectImport(input)
    const preparedSite = Object.values(prepared.graph.nodes).find((node) => node.type === 'site')

    expect(prepared.meta.id).toBe('struct-ifc-house')
    expect(prepared.meta.startMode).toBe('import')
    expect(preparedSite?.id).toBe(site.id)
    expect(preparedSite?.metadata).toMatchObject({
      ifcType: 'IFCSITE',
      globalId: 'guid-site',
      structProjectId: 'struct-ifc-house',
    })
    expect(input.graph.nodes[site.id]?.metadata).toEqual({
      ifcType: 'IFCSITE',
      globalId: 'guid-site',
    })
  })
})
