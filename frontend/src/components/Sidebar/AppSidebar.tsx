import { Link as RouterLink } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"

import { SidebarAppearance } from "@/components/Common/Appearance"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import { getNavigationEntries } from "@/config/tool-navigation"
import useAuth from "@/hooks/useAuth"
import { Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const items = getNavigationEntries(currentUser)
  const { t } = useTranslation()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="group-data-[collapsible=icon]:hidden">
        <RouterLink to="/" className="flex flex-col gap-2 px-2 pt-4 pb-2">
          <span className="text-heading text-foreground transition-colors hover:text-primary">
            {t("app.name")}
          </span>
          <span className="h-px w-10 bg-border" />
        </RouterLink>
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
