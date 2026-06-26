import { createFileRoute, Outlet, redirect, useMatches } from "@tanstack/react-router"

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
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (isLoggedIn()) return

    // 暂不实现企业微信 OAuth 自动登录
    // if (isWecomBrowser()) {
    //   redirectToWecomOAuth()
    //   await new Promise<never>(() => {})
    // }

    throw redirect({ to: "/login" })
  },
})

function Layout() {
  const matches = useMatches()
  const isExamDetail = matches.some(
    (m) => m.routeId === "/_layout/exams/$examId",
  )

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-svh bg-gradient-to-b from-background to-muted/30">
        <header className="bg-background/95 supports-[backdrop-filter]:bg-background/85 sticky top-0 z-20 flex h-16 shrink-0 items-center gap-2 border-b px-4 backdrop-blur">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
        </header>
        <main
          className={cn(
            "relative z-0 flex-1 p-6 md:p-8",
            isExamDetail && "overflow-hidden",
          )}
        >
          <div className={cn(isExamDetail ? "h-full" : "mx-auto max-w-7xl")}>
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
