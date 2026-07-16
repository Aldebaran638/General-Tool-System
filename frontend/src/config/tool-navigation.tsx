import type {
  NavigationEntry,
  NavigationGroup,
  NavigationTool,
} from "@/tools/registry"
export type { NavigationEntry, NavigationGroup, NavigationTool }

import { Home, Settings, Users } from "lucide-react"
import { toolRegistry } from "@/tools/registry"

/**
 * Platform-level navigation entries.
 * These are NOT tool modules; they are core platform features
 * that always exist regardless of which tools are registered.
 */
const PLATFORM_NAVIGATION: NavigationEntry[] = [
  {
    kind: "tool",
    icon: Home,
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

  // Add platform entries that pass permission check
  for (const entry of PLATFORM_NAVIGATION) {
    if (entry.kind === "tool") {
      if (entry.requiresSuperuser && !context.isSuperuser) {
        continue
      }
      entries.push(entry)
    }
  }

  // Add tool entries from registry (e.g. notification if it registers navigation)
  const toolEntries = toolRegistry.getNavigationEntries(context)
  entries.push(...toolEntries)

  return entries
}
