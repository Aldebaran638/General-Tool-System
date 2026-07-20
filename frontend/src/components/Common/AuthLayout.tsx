import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { Footer } from "./Footer"
import { Briefcase, ListTodo, CheckCircle2, Users } from "lucide-react"
import { useEffect, useRef, useState } from "react"

interface AuthLayoutProps {
  children: React.ReactNode
}

interface StatItemProps {
  value: number
  suffix?: string
  label: string
  duration?: number
  icon: React.ReactNode
  gradient: string
}

interface PublicStats {
  total_projects: number
  total_tasks: number
  completed_tasks: number
  total_members: number
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

function StatItem({ value, suffix = "", label, duration = 1500, icon, gradient }: StatItemProps) {
  const count = useCountUp(value, duration)
  return (
    <div className={`flex flex-col items-center rounded-xl bg-gradient-to-br ${gradient} p-4 backdrop-blur-sm transition-all hover:scale-[1.02] hover:bg-white/20 border border-white/10`}>
      <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white shadow-sm">{icon}</div>
      <div className="text-3xl font-extrabold text-white tabular-nums">
        {count.toLocaleString()}
        {suffix}
      </div>
      <div className="mt-1 text-xs text-blue-100 font-medium">{label}</div>
    </div>
  )
}

const STAT_CONFIG: {
  key: keyof PublicStats
  suffix: string
  label: string
  icon: React.ReactNode
  gradient: string
}[] = [
  { key: "total_projects", suffix: "+", label: "项目总数", icon: <Briefcase className="h-5 w-5" />, gradient: "from-white/15 to-blue-400/10" },
  { key: "total_tasks", suffix: "", label: "任务总数", icon: <ListTodo className="h-5 w-5" />, gradient: "from-white/15 to-indigo-400/10" },
  { key: "completed_tasks", suffix: "+", label: "已完成任务", icon: <CheckCircle2 className="h-5 w-5" />, gradient: "from-white/15 to-emerald-400/10" },
  { key: "total_members", suffix: "", label: "团队成员", icon: <Users className="h-5 w-5" />, gradient: "from-white/15 to-violet-400/10" },
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
      <div className="relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center overflow-hidden bg-gradient-to-br from-teal-600 via-teal-800 to-emerald-950 dark:from-teal-900 dark:via-teal-950 dark:to-emerald-950">
        {/* Decorative background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-emerald-400/15 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-60 w-60 rounded-full bg-teal-300/10 blur-2xl" />
          <div className="absolute top-1/4 right-1/4 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
          <div className="absolute bottom-1/3 left-1/4 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex w-full max-w-md flex-col items-center gap-8 px-12">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="rounded-2xl bg-white/90 p-4 backdrop-blur-md border border-white/40 shadow-lg shadow-black/10">
              <Logo variant="full" className="h-12" asLink={false} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-wider">项目管理面板</h1>
              <p className="mt-2 text-blue-100">数据驱动的项目管理</p>
            </div>
          </div>

          {/* Stats highlights */}
          <div className="grid grid-cols-2 gap-4 w-full">
            {STAT_CONFIG.map(({ key, suffix, label, icon, gradient }) => (
              <StatItem
                key={key}
                value={stats?.[key] ?? 0}
                suffix={suffix}
                label={label}
                icon={icon}
                gradient={gradient}
              />
            ))}
          </div>

          <p className="flex items-center gap-1.5 text-sm text-blue-100/80 font-medium">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
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
