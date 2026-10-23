import { beforeEach, describe, expect, test } from 'bun:test'
import { type AnyNode, type AnyNodeId, LevelNode, StructuralMember } from '@pascal-app/core'
import { useScene } from '@pascal-app/editor'
import { syncSectionLibraryFromScene, useStructStore } from '../../components/struct/struct-store'
import {
  buildStructProjectScene,
  createStructProjectMeta,
  DEFAULT_STRUCT_PROJECT_DRAFT,
  readStructProjectMeta,
} from './project-store'
import {
  DEFAULT_BEAM_SECTIONS,
  DEFAULT_COLUMN_SECTIONS,
  type SectionLibrary,
} from './section-definitions'

const LEVEL_ID = 'level_store'

function member(id: string, memberType: 'beam' | 'column', sectionId: string | null): AnyNode {
  return StructuralMember.parse({
    id,
    parentId: LEVEL_ID,
    memberType,
    start: [0, 0, 0],
    end: memberType === 'column' ? [0, 3, 0] : [6, 0, 0],
    sectionId,
    section: memberType === 'column' ? 'HW300×300×10×15' : 'HN400×200×8×13',
    material: 'Q355',
  })
}

function load(...members: AnyNode[]): void {
  const level = LevelNode.parse({
    id: LEVEL_ID,
    children: members.map((item) => item.id),
  })
  useScene.setState({
    nodes: Object.fromEntries([level, ...members].map((node) => [node.id, node])) as Record<
      AnyNodeId,
      AnyNode
    >,
    rootNodeIds: [level.id as AnyNodeId],
    dirtyNodes: new Set(),
    readOnly: false,
  })
  useScene.temporal.getState().resume()
  useScene.temporal.getState().clear()
}

function loadProject() {
  const meta = createStructProjectMeta(DEFAULT_STRUCT_PROJECT_DRAFT, { id: 'struct-store-project' })
  const graph = buildStructProjectScene(meta, meta.id).graph
  useScene.setState({
    nodes: graph.nodes as Record<AnyNodeId, AnyNode>,
    rootNodeIds: graph.rootNodeIds as AnyNodeId[],
    dirtyNodes: new Set(),
    readOnly: false,
  })
  useScene.temporal.getState().resume()
  useScene.temporal.getState().clear()
}

beforeEach(() => {
  useScene.setState({ nodes: {}, rootNodeIds: [], dirtyNodes: new Set(), readOnly: false })
  useStructStore.getState().reset()
  useScene.temporal.getState().resume()
  useScene.temporal.getState().clear()
})

describe('struct project section store', () => {
  test('hydrates project libraries without carrying definitions across projects', () => {
    const first: SectionLibrary = {
      columns: [
        {
          ...DEFAULT_COLUMN_SECTIONS[0]!,
          id: 'CS-A',
          label: '混凝土 450×650',
          b: 450,
          h: 650,
          material: 'C35',
        },
      ],
      beams: DEFAULT_BEAM_SECTIONS,
      activeColumnSectionId: 'CS-A',
      activeBeamSectionId: 'BS-1',
    }
    const second: SectionLibrary = {
      columns: [
        {
          ...DEFAULT_COLUMN_SECTIONS[2]!,
          id: 'CS-B',
          label: 'HW350×350×12×19',
          b: 350,
          h: 350,
          tw: 12,
          tf: 19,
          material: 'Q390',
        },
      ],
      beams: [
        {
          ...DEFAULT_BEAM_SECTIONS[2]!,
          id: 'BS-B',
          label: 'H600×300×12×20',
          b: 300,
          h: 600,
          tw: 12,
          tf: 20,
          material: 'Q390',
        },
      ],
      activeColumnSectionId: 'CS-B',
      activeBeamSectionId: 'BS-B',
    }

    useStructStore.getState().hydrateSectionLibrary(first, 'project-a')
    expect(useStructStore.getState().columnSections.map((section) => section.id)).toEqual(['CS-A'])

    useStructStore.getState().reset()
    useStructStore.getState().hydrateSectionLibrary(second, 'project-b')
    expect(useStructStore.getState().columnSections.map((section) => section.id)).toEqual(['CS-B'])
    expect(useStructStore.getState().beamSections.map((section) => section.id)).toEqual(['BS-B'])
    expect(useStructStore.getState().sectionLibraryProjectId).toBe('project-b')
  })

  test('updates every linked member of the matching type in one scene step', () => {
    load(
      member('structural-member_column', 'column', 'CS-3'),
      member('structural-member_beam_same_id', 'beam', 'CS-3'),
      member('structural-member_legacy', 'column', null),
    )

    useStructStore.getState().updateColumnSection('CS-3', {
      b: 350,
      h: 350,
      tw: 12,
      tf: 19,
      material: 'Q390',
    })

    const nodes = useScene.getState().nodes
    expect(nodes['structural-member_column' as AnyNodeId]).toMatchObject({
      sectionId: 'CS-3',
      section: 'H350×350×12×19',
      material: 'Q390',
    })
    expect(nodes['structural-member_beam_same_id' as AnyNodeId]).toMatchObject({
      sectionId: 'CS-3',
      section: 'HN400×200×8×13',
      material: 'Q355',
    })
    expect(nodes['structural-member_legacy' as AnyNodeId]).toMatchObject({
      sectionId: null,
      section: 'HW300×300×10×15',
      material: 'Q355',
    })
    expect(useScene.temporal.getState().pastStates).toHaveLength(1)
  })

  test('refuses to delete a section that is still referenced and explains why', () => {
    load(member('structural-member_column', 'column', 'CS-3'))

    const result = useStructStore.getState().deleteColumnSection('CS-3')

    expect(result.deleted).toBe(false)
    expect(result.reason).toContain('正在被')
    expect(useStructStore.getState().columnSections.some((section) => section.id === 'CS-3')).toBe(
      true,
    )
    expect(useStructStore.getState().log.at(-1)?.text).toContain('正在被')
    expect(useScene.getState().nodes['structural-member_column' as AnyNodeId]).toMatchObject({
      sectionId: 'CS-3',
    })
  })

  test('writes definition and active-id changes into project metadata for autosave', () => {
    loadProject()

    useStructStore.getState().setActiveColumnSection('CS-1')
    useStructStore.getState().updateBeamSection('BS-3', {
      h: 450,
      tw: 9,
      tf: 14,
      material: 'Q390',
    })

    const meta = readStructProjectMeta({
      nodes: useScene.getState().nodes,
      rootNodeIds: useScene.getState().rootNodeIds,
    })
    expect(meta?.sectionLibrary.activeColumnSectionId).toBe('CS-1')
    expect(meta?.sectionLibrary.beams.find((section) => section.id === 'BS-3')).toMatchObject({
      label: 'H450×200×9×14',
      material: 'Q390',
    })
  })

  test('restores the store section library from scene metadata after undo', () => {
    loadProject()
    const meta = readStructProjectMeta({
      nodes: useScene.getState().nodes,
      rootNodeIds: useScene.getState().rootNodeIds,
    })!
    useStructStore.getState().hydrateSectionLibrary(meta.sectionLibrary, meta.id)
    const linkedBeam = Object.values(useScene.getState().nodes).find(
      (node) =>
        node.type === 'structural-member' &&
        node.memberType === 'beam' &&
        node.sectionId === 'BS-3',
    )
    expect(linkedBeam?.type).toBe('structural-member')

    useStructStore.getState().updateBeamSection('BS-3', {
      h: 450,
      tw: 9,
      tf: 14,
      material: 'Q390',
    })
    expect(
      useStructStore.getState().beamSections.find((section) => section.id === 'BS-3'),
    ).toMatchObject({ label: 'H450×200×9×14', material: 'Q390' })
    expect(useScene.getState().nodes[linkedBeam!.id as AnyNodeId]).toMatchObject({
      section: 'H450×200×9×14',
      material: 'Q390',
    })
    expect(useScene.temporal.getState().pastStates).toHaveLength(1)

    useScene.temporal.getState().undo()
    expect(useScene.getState().nodes[linkedBeam!.id as AnyNodeId]).toMatchObject({
      section: 'HN400×200×8×13',
      material: 'Q355',
    })
    expect(
      useStructStore.getState().beamSections.find((section) => section.id === 'BS-3'),
    ).toMatchObject({ label: 'H450×200×9×14', material: 'Q390' })

    expect(syncSectionLibraryFromScene(meta.id)).toBe(true)
    expect(
      useStructStore.getState().beamSections.find((section) => section.id === 'BS-3'),
    ).toMatchObject({ label: 'HN400×200×8×13', material: 'Q355' })
  })

  test('does not replace store arrays when scene metadata has the same deep library', () => {
    loadProject()
    const meta = readStructProjectMeta({
      nodes: useScene.getState().nodes,
      rootNodeIds: useScene.getState().rootNodeIds,
    })!
    useStructStore.getState().hydrateSectionLibrary(meta.sectionLibrary, meta.id)
    const columns = useStructStore.getState().columnSections
    const beams = useStructStore.getState().beamSections

    expect(syncSectionLibraryFromScene(meta.id)).toBe(false)
    expect(useStructStore.getState().columnSections).toBe(columns)
    expect(useStructStore.getState().beamSections).toBe(beams)
  })
})

describe('IFC import store', () => {
  test('starts with the IFC import dialog closed', () => {
    expect(useStructStore.getState().ifcImportOpen).toBe(false)
  })

  test('opens and closes the IFC import workflow from commands', () => {
    const store = useStructStore.getState()

    store.openIfcImport()
    expect(useStructStore.getState().ifcImportOpen).toBe(true)

    store.closeIfcImport()
    expect(useStructStore.getState().ifcImportOpen).toBe(false)
  })

  test('closes the IFC import workflow with all other panels', () => {
    useStructStore.getState().openIfcImport()

    useStructStore.getState().closeAllPanels()

    expect(useStructStore.getState().ifcImportOpen).toBe(false)
  })
})
