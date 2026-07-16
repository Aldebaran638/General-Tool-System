import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - 项目管理面板",
      },
    ],
  }),
})

function formatToday(): string {
  const now = new Date()
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${now.getFullYear()}年${pad(now.getMonth() + 1)}月${pad(now.getDate())}日 ${weekdays[now.getDay()]}`
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div className="flex flex-col gap-6">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-700 to-emerald-800 dark:from-teal-800 dark:via-teal-900 dark:to-emerald-950 px-6 py-8 md:px-10 md:py-10">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-60 w-60 rounded-full bg-emerald-400/15 blur-3xl" />
          <div className="absolute top-1/2 right-1/4 h-40 w-40 rounded-full bg-white/5 blur-2xl" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-white">
              欢迎回来，{currentUser?.full_name || currentUser?.email || "用户"}
            </h1>
            <p className="text-teal-100 text-sm mt-1">项目管理面板</p>
          </div>
          <div className="flex items-center gap-2 text-teal-100 bg-white/10 backdrop-blur-sm rounded-lg px-4 py-2 border border-white/10">
            <span className="text-sm font-medium">{formatToday()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
