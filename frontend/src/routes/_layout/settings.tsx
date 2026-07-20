import { createFileRoute } from "@tanstack/react-router"
import { User, Lock, AlertTriangle } from "lucide-react"
import { useTranslation } from "react-i18next"

import i18n from "@/i18n"
import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  { value: "my-profile", titleKey: "settings.tabs.profile", component: UserInformation, icon: User },
  { value: "password", titleKey: "settings.tabs.password", component: ChangePassword, icon: Lock },
  { value: "danger-zone", titleKey: "settings.tabs.dangerZone", component: DeleteAccount, icon: AlertTriangle },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("nav.settings")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function UserSettings() {
  const { t } = useTranslation()
  const { user: currentUser } = useAuth()
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig
    : tabsConfig.filter((tab) => tab.value !== "danger-zone")

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("settings.title")}</h1>
        <p className="text-muted-foreground">
          {t("settings.description")}
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="gap-2">
              <tab.icon className="h-4 w-4" />
              {t(tab.titleKey)}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
