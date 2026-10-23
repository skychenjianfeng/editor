import { describe, expect, test } from 'bun:test'
import { readIfcSource } from './source'

const EMPTY_SOURCE = {
  ifcType: null,
  globalId: null,
  expressId: null,
  typeName: null,
  material: null,
}

describe('readIfcSource', () => {
  test('reads converter metadata into the imported-mesh source shape', () => {
    expect(
      readIfcSource({
        ifcType: 'IFCBEAM',
        globalId: '0YvctVUKr0kugbFTf53O9L',
        expressID: 42,
        typeName: 'Beam Type',
        material: 'Steel',
      }),
    ).toEqual({
      ifcType: 'IFCBEAM',
      globalId: '0YvctVUKr0kugbFTf53O9L',
      expressId: 42,
      typeName: 'Beam Type',
      material: 'Steel',
    })
  })

  test('returns null for missing source fields', () => {
    expect(readIfcSource({ ifcType: 'IFCBEAM' })).toEqual({
      ...EMPTY_SOURCE,
      ifcType: 'IFCBEAM',
    })
  })

  test('returns null for source fields with the wrong type', () => {
    expect(
      readIfcSource({
        ifcType: 7,
        globalId: false,
        expressID: '42',
        typeName: ['Beam Type'],
        material: { name: 'Steel' },
      }),
    ).toEqual(EMPTY_SOURCE)
  })

  test('does not throw for non-object metadata', () => {
    expect(readIfcSource(null)).toEqual(EMPTY_SOURCE)
    expect(readIfcSource('not metadata')).toEqual(EMPTY_SOURCE)
    expect(readIfcSource([])).toEqual(EMPTY_SOURCE)
  })
})
