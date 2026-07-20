import { useState } from "react"
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import {
  isLoggedIn,
} from "@/hooks/useAuth"
import { NotificationBell } from "@/components/NotificationBell"
import { NotificationDrawer } from "@/components/NotificationDrawer"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (isLoggedIn()) return

    throw redirect({ to: "/login" })
  },
})

function Layout() {
  const { t } = useTranslation()
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-svh bg-background">
        <header className="bg-background sticky top-0 z-20 flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">{t("nav.menu")}</span>
          <div className="ml-auto flex items-center gap-2">
            <NotificationBell onClick={() => setDrawerOpen(true)} />
          </div>
        </header>
        <main className="relative z-0 flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
      <NotificationDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </SidebarProvider>
  )
}
