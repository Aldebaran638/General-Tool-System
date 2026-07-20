import { Briefcase, CheckCircle2, ListTodo, Users } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Appearance } from "@/components/Common/Appearance"
import { LanguageSwitcher } from "@/components/Common/LanguageSwitcher"
import { Footer } from "./Footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

interface StatItemProps {
  value: number
  suffix?: string
  label: string
  duration?: number
  icon: React.ReactNode
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
      const eased = 1 - (1 - progress) ** 4
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

function StatItem({
  value,
  suffix = "",
  label,
  duration = 1500,
  icon,
}: StatItemProps) {
  const count = useCountUp(value, duration)
  return (
    <div className="flex flex-col items-center rounded-md bg-card border border-border p-5 transition-colors hover:border-primary/40">
      <div className="mb-3 flex h-9 w-9 items-center justify-center text-primary">
        {icon}
      </div>
      <div className="text-2xl font-semibold text-foreground tabular-nums tracking-wide">
        {count.toLocaleString()}
        {suffix}
      </div>
      <div className="mt-1 text-xs font-light text-muted-foreground">
        {label}
      </div>
    </div>
  )
}

const STAT_CONFIG: {
  key: keyof PublicStats
  suffix: string
  translationKey: string
  icon: React.ReactNode
}[] = [
  {
    key: "total_projects",
    suffix: "+",
    translationKey: "stats.totalProjects",
    icon: <Briefcase className="h-5 w-5" strokeWidth={1.5} />,
  },
  {
    key: "total_tasks",
    suffix: "",
    translationKey: "stats.totalTasks",
    icon: <ListTodo className="h-5 w-5" strokeWidth={1.5} />,
  },
  {
    key: "completed_tasks",
    suffix: "+",
    translationKey: "stats.completedTasks",
    icon: <CheckCircle2 className="h-5 w-5" strokeWidth={1.5} />,
  },
  {
    key: "total_members",
    suffix: "",
    translationKey: "stats.teamMembers",
    icon: <Users className="h-5 w-5" strokeWidth={1.5} />,
  },
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
  const { t } = useTranslation()
  const [stats, setStats] = useState<PublicStats | null>(null)

  useEffect(() => {
    fetchPublicStats()
      .then(setStats)
      .catch(() => {
        // Gracefully degrade: stats panel remains at zero on error.
      })
  }, [])

  return (
    <div className="grid min-h-svh bg-background lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center overflow-hidden px-12">
        <div className="relative z-10 flex w-full max-w-md flex-col items-center gap-10">
          <div className="flex flex-col items-center gap-5 text-center">
            <div>
              <h1 className="title-with-line text-display text-foreground">
                {t("app.name")}
              </h1>
              <p className="mt-3 text-base font-light text-muted-foreground tracking-wide">
                {t("app.subtitle")}
              </p>
            </div>
          </div>

          {/* Stats highlights */}
          <div className="grid grid-cols-2 gap-4 w-full">
            {STAT_CONFIG.map(({ key, suffix, translationKey, icon }) => (
              <StatItem
                key={key}
                value={stats?.[key] ?? 0}
                suffix={suffix}
                label={t(translationKey)}
                icon={icon}
              />
            ))}
          </div>

          <p className="flex items-center gap-2 text-sm font-light text-muted-foreground">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary" />
            {t("dashboard.liveData")}
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-col gap-4 p-6 md:p-10 lg:p-12">
        <div className="flex justify-end items-center gap-3">
          <LanguageSwitcher />
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm rounded-md bg-card border border-border p-8 md:p-10">
            {children}
          </div>
        </div>
        <Footer />
      </div>
    </div>
  )
}
