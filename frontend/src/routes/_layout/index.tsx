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
      <div className="relative overflow-hidden rounded-md bg-white border border-[#EAE6DF] px-6 py-8 md:px-10 md:py-10">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-[#2A2A2A] tracking-wide">
              欢迎回来，{currentUser?.full_name || currentUser?.email || "用户"}
            </h1>
            <p className="text-sm font-light text-[#6B6B6B] mt-2">项目管理面板</p>
          </div>
          <div className="flex items-center gap-2 text-[#6B6B6B] bg-[#FAF8F5] rounded-md px-4 py-2 border border-[#EAE6DF]">
            <span className="text-sm font-light">{formatToday()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
