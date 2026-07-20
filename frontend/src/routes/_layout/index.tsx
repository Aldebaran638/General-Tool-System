import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import {
  Building2,
  FolderKanban,
  ListTodo,
  type LucideIcon,
  Settings,
  Target,
  Users,
  UsersRound,
} from "lucide-react"
import { useTranslation } from "react-i18next"
import { Card } from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"
import i18n from "@/i18n"

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

type QuickLink = {
  to: string
  icon: LucideIcon
  titleKey: string
  superuserOnly?: boolean
  memberOnly?: boolean
}

const QUICK_LINKS: QuickLink[] = [
  {
    to: "/okr",
    icon: Target,
    titleKey: "nav.okrOverview",
    superuserOnly: true,
  },
  {
    to: "/okr/my",
    icon: ListTodo,
    titleKey: "nav.myTasks",
  },
  {
    to: "/okr/department-board",
    icon: FolderKanban,
    titleKey: "nav.departmentBoard",
    superuserOnly: true,
  },
  {
    to: "/okr/people-board",
    icon: UsersRound,
    titleKey: "nav.peopleBoard",
    superuserOnly: true,
  },
  {
    to: "/admin",
    icon: Users,
    titleKey: "nav.users",
    superuserOnly: true,
  },
  {
    to: "/okr/departments",
    icon: Building2,
    titleKey: "nav.departments",
    superuserOnly: true,
  },
  {
    to: "/settings",
    icon: Settings,
    titleKey: "nav.settings",
    memberOnly: true,
  },
]

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

  const displayName =
    currentUser?.full_name || currentUser?.email || t("dashboard.user")

  const isSuperuser = currentUser?.is_superuser ?? false
  const quickLinks = QUICK_LINKS.filter((link) => {
    if (link.superuserOnly) {
      return isSuperuser
    }
    if (link.memberOnly) {
      return !isSuperuser
    }
    return true
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="relative overflow-hidden rounded-md bg-card border border-border px-6 py-8 md:px-10 md:py-10">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-foreground tracking-wide">
              {t("dashboard.welcome", { name: displayName })}
            </h1>
            <p className="text-sm font-light text-muted-foreground mt-2">
              {t("dashboard.subtitle")}
            </p>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground bg-secondary rounded-md px-4 py-2 border border-border">
            <span className="text-sm font-light">
              {formatToday(i18nInstance.language)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="text-subheading text-foreground">
          {t("dashboard.quickLinks")}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {quickLinks.map((link) => (
            <RouterLink key={link.to} to={link.to}>
              <Card className="h-full flex-row items-center gap-3 px-4 py-4 transition-colors hover:border-primary/40 hover:bg-accent/50">
                <link.icon className="size-5 shrink-0 text-primary" />
                <span className="text-body text-foreground">
                  {t(link.titleKey)}
                </span>
              </Card>
            </RouterLink>
          ))}
        </div>
      </div>
    </div>
  )
}
