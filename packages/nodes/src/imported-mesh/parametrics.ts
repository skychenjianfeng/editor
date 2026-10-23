import type { ParametricDescriptor } from '@pascal-app/core'
import type { ImportedMeshNode } from './schema'

export const importedMeshParametrics: ParametricDescriptor<ImportedMeshNode> = {
  groups: [],
  customPanel: () => import('./panel'),
}
