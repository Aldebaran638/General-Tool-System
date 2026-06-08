import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { Footer } from "./Footer"
import { useEffect, useRef, useState } from "react"

interface AuthLayoutProps {
  children: React.ReactNode
}

interface StatItemProps {
  value: number
  suffix?: string
  label: string
  duration?: number
}

interface PublicStats {
  total_trainees: number
  total_exams: number
  passed_exams: number
  total_departments: number
}

function useCountUp(end: number, duration = 1500) {
  const [count, setCount] = useState(0)
  const frameRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    const startTime = performance.now()
    const animate = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 4)
      setCount(Math.floor(eased * end))
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      }
    }
    frameRef.current = requestAnimationFrame(animate)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [end, duration])

  return count
}

function StatItem({ value, suffix = "", label, duration = 1500 }: StatItemProps) {
  const count = useCountUp(value, duration)
  return (
    <div className="flex flex-col items-center rounded-xl bg-white/10 p-4 backdrop-blur-sm transition-all hover:bg-white/20">
      <div className="text-2xl font-bold text-white tabular-nums">
        {count.toLocaleString()}
        {suffix}
      </div>
      <div className="mt-1 text-xs text-blue-100">{label}</div>
    </div>
  )
}

const STAT_CONFIG: { key: keyof PublicStats; suffix: string; label: string }[] = [
  { key: "total_trainees", suffix: "+", label: "累计培训人次" },
  { key: "total_exams", suffix: "", label: "考试场次" },
  { key: "passed_exams", suffix: "+", label: "考核通过" },
  { key: "total_departments", suffix: "", label: "参与部门" },
]

async function fetchPublicStats(): Promise<PublicStats> {
  const base = (import.meta.env.VITE_API_URL as string | undefined) || ""
  const res = await fetch(`${base}/api/v1/public/stats`)
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.status}`)
  }
  return res.json()
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const [stats, setStats] = useState<PublicStats | null>(null)

  useEffect(() => {
    fetchPublicStats()
      .then(setStats)
      .catch(() => {
        // Gracefully degrade: stats panel remains at zero on error.
      })
  }, [])

  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 dark:from-blue-900 dark:via-blue-950 dark:to-indigo-950">
        {/* Decorative background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-indigo-400/20 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-60 w-60 rounded-full bg-blue-400/10 blur-2xl" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex w-full max-w-md flex-col items-center gap-8 px-12">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
              <Logo variant="full" className="h-12 brightness-0 invert" asLink={false} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">课程培训及考核管理平台</h1>
              <p className="mt-2 text-blue-100">数据驱动的培训与考核管理</p>
            </div>
          </div>

          {/* Stats highlights */}
          <div className="grid grid-cols-2 gap-4 w-full">
            {STAT_CONFIG.map(({ key, suffix, label }) => (
              <StatItem
                key={key}
                value={stats?.[key] ?? 0}
                suffix={suffix}
                label={label}
              />
            ))}
          </div>

          <p className="flex items-center gap-1.5 text-xs text-blue-200/70">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            实时数据
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-between items-center">
          {/* Mobile logo */}
          <div className="lg:hidden">
            <Logo variant="full" className="h-8" />
          </div>
          <div className="ml-auto">
            <Appearance />
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
        <Footer />
      </div>
    </div>
  )
}
