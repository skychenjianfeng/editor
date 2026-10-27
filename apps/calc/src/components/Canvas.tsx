import { FileDown, ImageDown, Maximize2, MousePointer2, Ruler, ZoomIn, ZoomOut } from 'lucide-react'
import type { GeometryPayload, View } from '../api/calc'

export type Layers = { upright: boolean; level: boolean; brace: boolean; dim: boolean }

const CHIP_COLORS: Record<string, string> = {
  upright: '#e5484d',
  level: '#e5484d',
  brace: '#3e63dd',
  dim: '#30a46c',
}

export function Canvas({
  geometry,
  view,
  onView,
  layers,
  onLayers,
  onExport,
}: {
  geometry?: GeometryPayload
  view: View
  onView: (v: View) => void
  layers: Layers
  onLayers: (l: Layers) => void
  onExport?: (kind: 'dxf' | 'png') => void
}) {
  const bounds = geometry?.bounds ?? { minX: -1400, minY: -1200, maxX: 9400, maxY: 24600 }
  const width = Math.max(1, bounds.maxX - bounds.minX)
  const height = Math.max(1, bounds.maxY - bounds.minY)
  const flipY = (y: number) => bounds.maxY - y

  return (
    <section className="flex h-full flex-col bg-[color:var(--color-canvas)]">
      <div className="flex h-9 shrink-0 items-center gap-1 border-b border-white/10 bg-[#12161d] px-2">
        <div className="flex items-center gap-0.5 rounded-md bg-black/30 p-0.5">
          {(
            [
              ['正立面', 'elevation'],
              ['侧立面', 'side'],
              ['平面', 'plan'],
              ['剖面', 'section'],
            ] as [string, View][]
          ).map(([label, key]) => (
            <button
              key={label}
              onClick={() => onView(key as 'plan' | 'elevation')}
              className={`rounded px-2.5 py-1 text-[11px] transition-colors ${
                view === key ? 'bg-white/10 text-white' : 'text-white/45 hover:text-white/75'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="mx-2 h-4 w-px bg-white/10" />

        <button className="flex h-6 items-center gap-1 rounded px-1.5 text-[11px] text-white/60 hover:bg-white/5 hover:text-white/85">
          <MousePointer2 className="h-3 w-3" /> 选择
        </button>
        <button className="flex h-6 items-center gap-1 rounded px-1.5 text-[11px] text-white/60 hover:bg-white/5 hover:text-white/85">
          <Ruler className="h-3 w-3" /> 标注
        </button>

        <div className="ml-auto flex items-center gap-0.5">
          <button
            onClick={() => onExport?.('dxf')}
            title="导出 DXF"
            className="flex h-6 items-center gap-1 rounded px-1.5 text-[10px] text-white/50 hover:bg-white/5 hover:text-white/85"
          >
            <FileDown className="h-3 w-3" /> DXF
          </button>
          <button
            onClick={() => onExport?.('png')}
            title="导出 PNG"
            className="flex h-6 items-center gap-1 rounded px-1.5 text-[10px] text-white/50 hover:bg-white/5 hover:text-white/85"
          >
            <ImageDown className="h-3 w-3" /> PNG
          </button>
          <div className="mx-1 h-4 w-px bg-white/10" />
          <button className="grid h-6 w-6 place-items-center rounded text-white/50 hover:bg-white/5 hover:text-white/80">
            <ZoomOut className="h-3 w-3" />
          </button>
          <span className="tnum px-1 text-[10px] text-white/40">100%</span>
          <button className="grid h-6 w-6 place-items-center rounded text-white/50 hover:bg-white/5 hover:text-white/80">
            <ZoomIn className="h-3 w-3" />
          </button>
          <button className="grid h-6 w-6 place-items-center rounded text-white/50 hover:bg-white/5 hover:text-white/80">
            <Maximize2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      <div className="relative min-h-0 flex-1">
        <svg
          viewBox={`${bounds.minX} 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          className="h-full w-full"
        >
          <defs>
            <pattern id="grid" width="500" height="500" patternUnits="userSpaceOnUse">
              <path d="M500 0H0V500" fill="none" stroke="#1c2129" strokeWidth="1" />
            </pattern>
          </defs>
          <rect x={bounds.minX} y={0} width={width} height={height} fill="url(#grid)" />

          {geometry?.layers
            .filter((layer) => layers[layer.id as keyof Layers] !== false)
            .map((layer) => (
              <g key={layer.id}>
                {layer.items.map((item, i) => {
                  if (item.type === 'line') {
                    return (
                      <line
                        key={`${layer.id}-l-${i}`}
                        x1={item.x1}
                        y1={flipY(item.y1)}
                        x2={item.x2}
                        y2={flipY(item.y2)}
                        stroke={layer.color}
                        strokeWidth={layer.id === 'dim' ? 1 : 1.2}
                        vectorEffect="non-scaling-stroke"
                        opacity={layer.id === 'dim' ? 0.85 : 1}
                      />
                    )
                  }
                  if (item.type === 'circle') {
                    return (
                      <circle
                        key={`${layer.id}-c-${i}`}
                        cx={item.x}
                        cy={flipY(item.y)}
                        r={item.r}
                        fill={layer.color}
                      />
                    )
                  }
                  return (
                    <text
                      key={`${layer.id}-t-${i}`}
                      x={item.x}
                      y={flipY(item.y)}
                      fill={layer.color}
                      fontSize={item.size}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      transform={`rotate(${-item.rotation} ${item.x} ${flipY(item.y)})`}
                    >
                      {item.text}
                    </text>
                  )
                })}
              </g>
            ))}
        </svg>

        {!geometry && (
          <div className="absolute inset-0 grid place-items-center text-[12px] text-white/40">
            正在生成几何…
          </div>
        )}

        <div className="absolute bottom-2 left-2 flex items-center gap-3 rounded-md border border-white/10 bg-black/45 px-2 py-1 text-[10px] text-white/60 backdrop-blur">
          {[
            ['立杆', 'upright'],
            ['水平杆', 'level'],
            ['剪刀撑', 'brace'],
            ['尺寸', 'dim'],
          ].map(([label, key]) => {
            const on = layers[key as keyof Layers]
            return (
              <button
                key={key}
                onClick={() => onLayers({ ...layers, [key]: !on })}
                className={`flex items-center gap-1 ${on ? 'text-white/85' : 'text-white/30'}`}
              >
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: CHIP_COLORS[key], opacity: on ? 1 : 0.25 }}
                />
                {label}
              </button>
            )
          })}
        </div>

        <div className="absolute right-2 top-2 rounded border border-white/10 bg-black/40 px-2 py-1 text-[10px] text-white/50 backdrop-blur">
          单位 mm · 图层来自后端几何
        </div>
      </div>
    </section>
  )
}
