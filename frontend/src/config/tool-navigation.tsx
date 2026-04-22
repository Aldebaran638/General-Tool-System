import type { LucideIcon } from "lucide-react"
import { Briefcase, Home, Settings, Users } from "lucide-react"

type ToolPath =
  | "/"
  | "/items"
  | "/admin"
  | "/settings"

type NavigationVisibilityContext = {
  isSuperuser: boolean
}

type NavigationBase = {
  icon: LucideIcon
  title: string
}

export type NavigationTool = NavigationBase & {
  kind: "tool"
  path: ToolPath
  requiresSuperuser?: boolean
}

export type NavigationGroup = NavigationBase & {
  kind: "group"
  children: NavigationTool[]
  defaultExpanded?: boolean
}

export type NavigationEntry = NavigationTool | NavigationGroup

const navigationEntries: NavigationEntry[] = [
  {
    icon: Briefcase,
    title: "\u5de5\u4f5c\u53f0",
    kind: "group",
    defaultExpanded: true,
    children: [
      {
        kind: "tool",
        icon: Home,
        title: "\u4eea\u8868\u76d8",
        path: "/",
      },
      {
        kind: "tool",
        icon: Briefcase,
        title: "\u9879\u76ee\u7ba1\u7406",
        path: "/items",
      },
    ],
  },
  {
    kind: "group",
    icon: Settings,
    title: "\u7cfb\u7edf\u7ba1\u7406",
    defaultExpanded: true,
    children: [
      {
        kind: "tool",
        icon: Settings,
        title: "\u4e2a\u4eba\u8bbe\u7f6e",
        path: "/settings",
      },
      {
        kind: "tool",
        icon: Users,
        title: "\u7528\u6237\u7ba1\u7406",
        path: "/admin",
        requiresSuperuser: true,
      },
    ],
  },
]

function canAccessTool(
  tool: NavigationTool,
  context: NavigationVisibilityContext,
) {
  if (tool.requiresSuperuser && !context.isSuperuser) {
    return false
  }

  return true
}

export function getNavigationEntries(
  currentUser?: {
    is_superuser?: boolean
  } | null,
): NavigationEntry[] {
  const context: NavigationVisibilityContext = {
    isSuperuser: currentUser?.is_superuser ?? false,
  }

  return navigationEntries.reduce<NavigationEntry[]>((entries, entry) => {
    if (entry.kind === "tool") {
      if (canAccessTool(entry, context)) {
        entries.push(entry)
      }

      return entries
    }

    const children = entry.children.filter((child) =>
      canAccessTool(child, context),
    )

    if (children.length === 0) {
      return entries
    }

    entries.push({ ...entry, children })
    return entries
  }, [])
}
