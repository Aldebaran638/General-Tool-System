import { createFileRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"

import i18n from "@/i18n"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("nav.dashboard")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function formatToday(locale: string): string {
  const now = new Date()
  return new Intl.DateTimeFormat(locale === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    weekday: "short",
  }).format(now)
}

function Dashboard() {
  const { t, i18n: i18nInstance } = useTranslation()
  const { user: currentUser } = useAuth()

  const displayName = currentUser?.full_name || currentUser?.email || t("dashboard.user")

  return (
    <div className="flex flex-col gap-6">
      <div className="relative overflow-hidden rounded-md bg-white border border-[#EAE6DF] px-6 py-8 md:px-10 md:py-10">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-[#2A2A2A] tracking-wide">
              {t("dashboard.welcome", { name: displayName })}
            </h1>
            <p className="text-sm font-light text-[#6B6B6B] mt-2">{t("dashboard.subtitle")}</p>
          </div>
          <div className="flex items-center gap-2 text-[#6B6B6B] bg-[#FAF8F5] rounded-md px-4 py-2 border border-[#EAE6DF]">
            <span className="text-sm font-light">{formatToday(i18nInstance.language)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
