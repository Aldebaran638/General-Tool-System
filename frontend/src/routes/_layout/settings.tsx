import { createFileRoute } from "@tanstack/react-router"

import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useI18n } from "@/i18n"
import useAuth from "@/hooks/useAuth"
import LanguageSelector from "@/components/UserSettings/LanguageSelector"

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: "Settings - 发票管理系统",
      },
    ],
  }),
})

function UserSettings() {
  const { t } = useI18n()
  const { user: currentUser } = useAuth()

  const tabsConfig = [
    {
      value: "my-profile",
      title: t("settings.myProfile"),
      component: UserInformation,
    },
    {
      value: "password",
      title: t("settings.password"),
      component: ChangePassword,
    },
    {
      value: "danger-zone",
      title: t("settings.dangerZone"),
      component: DeleteAccount,
    },
  ]

  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.slice(0, 3)
    : tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("settings.title")}
        </h1>
        <p className="text-muted-foreground">{t("settings.subtitle")}</p>
      </div>

      <LanguageSelector />

      <Tabs defaultValue="my-profile">
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
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
