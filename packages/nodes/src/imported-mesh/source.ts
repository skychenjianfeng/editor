export type IfcSource = {
  ifcType: string | null
  globalId: string | null
  expressId: number | null
  typeName: string | null
  material: string | null
}

const EMPTY_IFC_SOURCE: IfcSource = {
  ifcType: null,
  globalId: null,
  expressId: null,
  typeName: null,
  material: null,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function readString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function readExpressId(value: unknown): number | null {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0 ? value : null
}

/** Read the converter's flat IFC metadata without trusting persisted JSON. */
export function readIfcSource(metadata: unknown): IfcSource {
  if (!isRecord(metadata)) return EMPTY_IFC_SOURCE

  return {
    ifcType: readString(metadata.ifcType),
    globalId: readString(metadata.globalId),
    expressId: readExpressId(metadata.expressID),
    typeName: readString(metadata.typeName),
    material: readString(metadata.material),
  }
}
