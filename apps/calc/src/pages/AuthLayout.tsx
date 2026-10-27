import { FileCheck2, Ruler, ShieldCheck } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function AuthLayout({
  mode,
  title,
  description,
  children,
}: {
  mode: 'login' | 'register'
  title: string
  description: string
  children: ReactNode
}) {
  const reducedMotion = useReducedMotion()
  return (
    <main className="grid min-h-screen bg-[#f7f7f8] text-[#18181b] min-[820px]:grid-cols-[minmax(340px,0.88fr)_minmax(440px,1.12fr)]">
      <section className="relative overflow-hidden bg-[#0d241f] px-6 py-8 text-white min-[820px]:flex min-[820px]:min-h-screen min-[820px]:flex-col min-[820px]:justify-between min-[820px]:px-10 min-[820px]:py-10">
        <div
          aria-hidden="true"
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />
        <div className="relative">
          <Link
            to={mode === 'login' ? '/login' : '/register'}
            className="inline-flex items-center gap-3"
          >
            <span className="grid size-10 place-items-center rounded-lg bg-[#d9f99d] text-sm font-black text-[#173c32]">
              PM
            </span>
            <span>
              <span className="block text-sm font-semibold tracking-[0.18em]">PM STUDIO</span>
              <span className="mt-0.5 block text-xs text-white/55">结构与脚手架安全计算</span>
            </span>
          </Link>
          <div className="mt-10 max-w-md min-[820px]:mt-20">
            <p className="text-xs font-medium tracking-[0.22em] text-[#bef264]">工程计算工作区</p>
            <h1 className="mt-3 text-3xl leading-tight font-semibold tracking-tight min-[820px]:text-4xl">
              从项目到计算书，
              <br />
              保持在同一个上下文。
            </h1>
            <p className="mt-4 text-sm leading-6 text-white/65">
              为结构工程师整理的轻量计算与项目跟踪工作台。参数、方案、校核结论按项目归档。
            </p>
          </div>
        </div>
        <ul className="relative mt-8 grid gap-2 text-xs text-white/70 min-[820px]:mt-12 min-[820px]:gap-3">
          <li className="flex items-center gap-2.5">
            <Ruler className="size-4 text-[#bef264]" />
            参数化构件计算与图纸联动
          </li>
          <li className="flex items-center gap-2.5">
            <ShieldCheck className="size-4 text-[#bef264]" />
            计算结果与规范条文可追溯
          </li>
          <li className="flex items-center gap-2.5">
            <FileCheck2 className="size-4 text-[#bef264]" />
            项目方案集中归档，不丢失工况
          </li>
        </ul>
      </section>

      <section className="grid items-center px-4 py-8 min-[820px]:px-10">
        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="mx-auto w-full max-w-[430px] rounded-xl border border-[#e2e4e7] bg-white p-6 shadow-[0_18px_60px_rgba(24,24,27,0.08)] sm:p-8"
        >
          <p className="text-xs font-semibold tracking-[0.18em] text-[#176b55]">
            {mode === 'login' ? '账号登录' : '创建账号'}
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-[#71717a]">{description}</p>
          <div className="mt-6">{children}</div>
        </motion.div>
      </section>
    </main>
  )
}
