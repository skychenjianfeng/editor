import { describe, expect, test } from 'bun:test'
import { ImportedMeshNode } from '@pascal-app/core'
import { importedMeshDefinition } from './definition'

describe('imported mesh editing', () => {
  test('keeps its existing capabilities and adds three-axis movement', () => {
    expect(importedMeshDefinition.capabilities).toMatchObject({
      selectable: { hitVolume: 'bbox' },
      movable: { axes: ['x', 'y', 'z'], gridSnap: true },
      duplicable: true,
      deletable: true,
      presettable: false,
    })
  })

  test('registers the IFC inspector without changing hidden presentation', () => {
    expect(importedMeshDefinition.parametrics?.customPanel).toBeFunction()
    expect(importedMeshDefinition.presentation?.hidden).toBe(true)
  })

  test('keeps geometry and floorplan rendering available', () => {
    const node = ImportedMeshNode.parse({
      id: 'imesh_definition',
      position: [10, 2, 20],
      primitives: [
        {
          positions: [0, 0, 0, 2, 0, 0, 0, 3, 4],
          indices: [0, 1, 2],
        },
      ],
    })

    expect(importedMeshDefinition.geometry?.(node).children).toHaveLength(1)
    expect(importedMeshDefinition.floorplan?.(node, {})).toMatchObject({
      kind: 'polygon',
      points: [
        [10, 20],
        [12, 20],
        [12, 24],
        [10, 24],
      ],
    })
  })
})
