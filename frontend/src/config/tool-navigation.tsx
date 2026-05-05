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
import "@/tools/finance/purchase_records"
import "@/tools/finance/invoice_files"
import "@/tools/finance/invoice_matching"
import "@/tools/finance/reimbursement_exports"

/**
 * Platform-level navigation entries.
 * These are NOT tool modules; they are core platform features
 * that always exist regardless of which tools are registered.
 */
function buildPlatformNavigation(t: (key: string) => string): NavigationGroup[] {
  return [
    {
      kind: "group",
      id: "platform",
      icon: Home,
      title: t("navigation.platform"),
      defaultExpanded: true,
      children: [
        {
          kind: "tool",
          icon: LayoutDashboard,
          title: t("navigation.dashboard"),
          path: "/",
        },
        {
          kind: "tool",
          icon: Settings,
          title: t("navigation.userSettings"),
          path: "/settings",
        },
        {
          kind: "tool",
          icon: Users,
          title: t("navigation.userManagement"),
          path: "/admin",
          requiresSuperuser: true,
        },
      ],
    },
  ]
}

export function getNavigationEntries(
  currentUser?: {
    is_superuser?: boolean
  } | null,
  t?: (key: string) => string,
): NavigationEntry[] {
  const _t = t || ((key: string) => key)
  const context = {
    isSuperuser: currentUser?.is_superuser ?? false,
  }

  // Start with platform entries
  const entries: NavigationEntry[] = []

  // Add platform groups with child-level permission checks
  for (const group of buildPlatformNavigation(_t)) {
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
  const toolEntries = toolRegistry.getNavigationEntries(context, _t)
  entries.push(...toolEntries)

  return entries
}
