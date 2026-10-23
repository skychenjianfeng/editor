import { type AnyNode, type AnyNodeId, SiteNode } from '@pascal-app/core'
import type { SceneGraph } from '@pascal-app/editor'
import {
  createStructProjectMeta,
  DEFAULT_STRUCT_PROJECT_DRAFT,
  type StructProjectMeta,
  withStructProjectMetadata,
} from './project-store'

export type IfcGraphSummary = {
  nodeCount: number
  levelCount: number
  importedMeshCount: number
  typeCounts: Record<string, number>
  sourceFile: string
}

export type IfcProjectImport = {
  meta: StructProjectMeta
  graph: SceneGraph
  summary: IfcGraphSummary
}

type MutableNode = AnyNode & {
  parentId: string | null
  children?: string[]
}

function uniqueIds(ids: readonly string[]): AnyNodeId[] {
  return [...new Set(ids)] as AnyNodeId[]
}

export function normalizeIfcSceneGraph(graph: SceneGraph): SceneGraph {
  const cloned = structuredClone(graph) as SceneGraph
  const nodes = cloned.nodes as Record<string, MutableNode | undefined>
  const existingRootIds = uniqueIds(cloned.rootNodeIds).filter((id) => Boolean(nodes[id]))
  const rootSites = existingRootIds.filter((id) => nodes[id]?.type === 'site')

  if (rootSites.length === 1) {
    const rootSiteId = rootSites[0]!
    const rootSite = nodes[rootSiteId]!
    const listedChildren = Array.isArray(rootSite.children)
      ? rootSite.children.filter((id) => Boolean(nodes[id]) && id !== rootSiteId)
      : []
    const parentedChildren = Object.entries(nodes)
      .filter(([id, node]) => id !== rootSiteId && node?.parentId === rootSiteId)
      .map(([id]) => id)
    const children = uniqueIds([
      ...listedChildren,
      ...parentedChildren,
      ...existingRootIds.filter((id) => id !== rootSiteId),
    ])

    rootSite.children = children
    for (const childId of children) {
      const child = nodes[childId]
      if (child) child.parentId = rootSiteId
    }
    cloned.rootNodeIds = [rootSiteId]
    return cloned
  }

  const rootSite = SiteNode.parse({
    polygon: { type: 'polygon', points: [] },
  })
  const children = uniqueIds(existingRootIds)
  rootSite.children = children

  for (const childId of children) {
    const child = nodes[childId]
    if (child) child.parentId = rootSite.id
  }

  nodes[rootSite.id] = rootSite as MutableNode
  cloned.rootNodeIds = [rootSite.id]
  return cloned
}

export function summarizeIfcGraph(graph: SceneGraph, sourceFile: string): IfcGraphSummary {
  let levelCount = 0
  let importedMeshCount = 0
  const typeCounts: Record<string, number> = {}

  for (const node of Object.values(graph.nodes) as AnyNode[]) {
    typeCounts[node.type] = (typeCounts[node.type] ?? 0) + 1
    if (node.type === 'level') levelCount += 1
    if (node.type === 'imported-mesh') importedMeshCount += 1
  }

  return {
    nodeCount: Object.keys(graph.nodes).length,
    levelCount,
    importedMeshCount,
    typeCounts,
    sourceFile,
  }
}

export function prepareIfcProjectImport(input: {
  graph: SceneGraph
  projectName: string
  sourceFile: string
  projectId?: string
  now?: Date
}): IfcProjectImport {
  const meta = createStructProjectMeta(
    {
      ...DEFAULT_STRUCT_PROJECT_DRAFT,
      name: input.projectName.trim() || input.sourceFile.replace(/\.ifc$/i, ''),
      startMode: 'import',
    },
    { id: input.projectId, now: input.now },
  )
  const normalized = normalizeIfcSceneGraph(input.graph)
  const graph = withStructProjectMetadata(normalized, meta)
  return { meta, graph, summary: summarizeIfcGraph(graph, input.sourceFile) }
}
