import { ArrowLeft, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'

export function RecycleBinPage() {
  return (
    <div className="mx-auto w-full max-w-[960px] px-4 py-7 text-[#18181b] sm:px-6 sm:py-9">
      <section>
        <p className="text-[11px] font-semibold tracking-[0.18em] text-[#176b55]">RECYCLE BIN</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">回收站</h1>
        <p className="mt-2 text-sm leading-6 text-[#71717a]">
          用于集中查看后续支持恢复的项目和方案。
        </p>
      </section>

      <section className="mt-6 grid min-h-72 place-items-center rounded-lg border border-dashed bg-white px-6 py-10 text-center">
        <div>
          <div className="mx-auto grid size-12 place-items-center rounded-full bg-[#f4f4f5] text-[#71717a]">
            <Trash2 className="size-5" />
          </div>
          <h2 className="mt-4 text-base font-semibold">回收站尚未启用</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#71717a]">
            当前删除项目仍会永久移除项目及其方案。后续启用恢复能力后，这里将展示可恢复内容。
          </p>
          <Button asChild variant="outline" size="sm" className="mt-5">
            <Link to="/workspace/projects">
              <ArrowLeft />
              返回项目管理
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
