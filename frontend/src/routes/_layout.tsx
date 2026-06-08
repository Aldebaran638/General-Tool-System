import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import {
  isLoggedIn,
  isWecomBrowser,
  redirectToWecomOAuth,
} from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (isLoggedIn()) return

    if (isWecomBrowser()) {
      // Inside WeCom: trigger OAuth flow instead of showing the login form.
      // Full-page navigation hands control to WeCom; the browser won't render
      // this route at all, so we suspend with a never-resolving Promise.
      redirectToWecomOAuth()
      await new Promise<never>(() => {})
    }

    throw redirect({ to: "/login" })
  },
})

function Layout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-svh bg-gradient-to-b from-background to-muted/30">
        <header className="bg-background/95 supports-[backdrop-filter]:bg-background/85 sticky top-0 z-20 flex h-16 shrink-0 items-center gap-2 border-b px-4 backdrop-blur">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">菜单</span>
        </header>
        <main className="relative z-0 flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
