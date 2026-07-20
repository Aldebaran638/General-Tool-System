import { SidebarAppearance } from "@/components/Common/Appearance"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { getNavigationEntries } from "@/config/tool-navigation"
import useAuth from "@/hooks/useAuth"
import { Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const items = getNavigationEntries(currentUser)

  return (
    <Sidebar collapsible="icon">
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
