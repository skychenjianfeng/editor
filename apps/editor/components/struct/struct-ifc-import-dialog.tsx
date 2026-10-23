'use client'

import { useStructStore } from './struct-store'

export function StructIfcImportDialog() {
  const open = useStructStore((state) => state.ifcImportOpen)
  if (!open) return null
  return <div data-testid="struct-ifc-import-dialog">IFC import</div>
}
