'use client'

import { type ImportedMeshNode, useScene } from '@pascal-app/core'
import {
  ActionButton,
  ActionGroup,
  createEditorApi,
  PanelSection,
  PanelWrapper,
  triggerSFX,
} from '@pascal-app/editor'
import { useViewer } from '@pascal-app/viewer'
import { Eye, EyeOff, Move, Trash2 } from 'lucide-react'
import { useCallback } from 'react'
import { readIfcSource } from './source'

function SourceRow({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="flex min-w-0 items-start justify-between gap-3 px-1 py-1 text-xs">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="min-w-0 break-all text-right font-mono text-foreground">{value ?? '—'}</span>
    </div>
  )
}

export function ImportedMeshPanelBody({
  node,
  onDelete,
  onMove,
  onUpdate,
  readOnly,
}: {
  node: ImportedMeshNode
  onDelete: () => void
  onMove: () => void
  onUpdate: (patch: Partial<ImportedMeshNode>) => void
  readOnly: boolean
}) {
  const source = readIfcSource(node.metadata)
  const visible = node.visible !== false

  return (
    <>
      <PanelSection title="基本">
        <label className="px-1 text-muted-foreground text-xs" htmlFor={`${node.id}-name`}>
          名称
        </label>
        <input
          aria-label="名称"
          className="h-9 rounded-lg border border-border/50 bg-background px-3 text-foreground text-xs outline-none focus:border-ring disabled:opacity-50"
          disabled={readOnly}
          id={`${node.id}-name`}
          onChange={(event) => onUpdate({ name: event.currentTarget.value })}
          value={node.name ?? ''}
        />
      </PanelSection>

      <PanelSection title="IFC 导入实体">
        <div data-testid="imported-mesh-metadata">
          <SourceRow label="IFC 类型" value={source.ifcType} />
          <SourceRow label="GlobalId" value={source.globalId} />
          <SourceRow label="ExpressID" value={source.expressId} />
          <SourceRow label="来源类型" value={source.typeName} />
          <SourceRow label="材料" value={source.material} />
        </div>
        <p className="px-1 pt-1 text-muted-foreground text-xs leading-relaxed">
          几何按 IFC 保留；截面和结构计算参数暂不可编辑。
        </p>
      </PanelSection>

      <PanelSection title="操作">
        <ActionGroup>
          <ActionButton
            icon={visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            label={visible ? '隐藏' : '显示'}
            onClick={() => onUpdate({ visible: !visible })}
          />
          <ActionButton
            data-testid="imported-mesh-move"
            icon={<Move className="h-4 w-4" />}
            label="移动"
            onClick={onMove}
          />
        </ActionGroup>
        <ActionGroup>
          <ActionButton
            className="border-red-500/40 text-red-700 hover:bg-red-500/15 dark:text-red-200"
            icon={<Trash2 className="h-4 w-4" />}
            label="删除"
            onClick={onDelete}
          />
        </ActionGroup>
      </PanelSection>
    </>
  )
}

export default function ImportedMeshPanel({ node }: { node: ImportedMeshNode }) {
  const deleteNode = useScene((state) => state.deleteNode)
  const readOnly = useScene((state) => state.readOnly)
  const setSelection = useViewer((state) => state.setSelection)
  const updateNode = useScene((state) => state.updateNode)

  const close = useCallback(() => {
    setSelection({ selectedIds: [] })
  }, [setSelection])

  const move = useCallback(() => {
    triggerSFX('sfx:item-pick')
    createEditorApi().engageMove(node)
    setSelection({ selectedIds: [] })
  }, [node, setSelection])

  const update = useCallback(
    (patch: Partial<ImportedMeshNode>) => {
      updateNode(node.id, patch)
    },
    [node.id, updateNode],
  )

  const remove = useCallback(() => {
    triggerSFX('sfx:structure-delete')
    deleteNode(node.id)
    setSelection({ selectedIds: [] })
  }, [deleteNode, node.id, setSelection])

  return (
    <PanelWrapper
      icon="/icons/item.webp"
      onClose={close}
      title={node.name || 'IFC 导入实体'}
      width={320}
    >
      <ImportedMeshPanelBody
        node={node}
        onDelete={remove}
        onMove={move}
        onUpdate={update}
        readOnly={readOnly}
      />
    </PanelWrapper>
  )
}
