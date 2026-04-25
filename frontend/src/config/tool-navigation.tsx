import type {
  NavigationEntry,
  NavigationGroup,
  NavigationTool,
} from "@/tools/registry"
export type { NavigationEntry, NavigationGroup, NavigationTool }

import { Home, LayoutDashboard, Settings, Users } from "lucide-react"
import { toolRegistry } from "@/tools/registry"

// Import all tool modules to trigger their self-registration
// This is the ONLY place where tool modules should be explicitly imported.
import "@/tools/workbench/project_management"
import "@/tools/finance/purchase_records"
import "@/tools/finance/invoice_files"

/**
 * Platform-level navigation entries.
 * These are NOT tool modules; they are core platform features
 * that always exist regardless of which tools are registered.
 */
const PLATFORM_NAVIGATION: NavigationGroup[] = [
  {
    kind: "group",
    icon: Home,
    title: "平台",
    defaultExpanded: true,
    children: [
      {
        kind: "tool",
        icon: LayoutDashboard,
        title: "仪表盘",
        path: "/",
      },
      {
        kind: "tool",
        icon: Settings,
        title: "个人设置",
        path: "/settings",
      },
      {
        kind: "tool",
        icon: Users,
        title: "用户管理",
        path: "/admin",
        requiresSuperuser: true,
      },
    ],
  },
]

export function getNavigationEntries(
  currentUser?: {
    is_superuser?: boolean
  } | null,
): NavigationEntry[] {
  const context = {
    isSuperuser: currentUser?.is_superuser ?? false,
  }

  // Start with platform entries
  const entries: NavigationEntry[] = []

  // Add platform groups with child-level permission checks
  for (const group of PLATFORM_NAVIGATION) {
    const children = group.children.filter((child) => {
      if (child.requiresSuperuser && !context.isSuperuser) {
        return false
      }
      return true
    })

    if (children.length > 0) {
      entries.push({
        ...group,
        children,
      })
    }
  }

  // Add tool entries from registry
  const toolEntries = toolRegistry.getNavigationEntries(context)
  entries.push(...toolEntries)

  return entries
}
