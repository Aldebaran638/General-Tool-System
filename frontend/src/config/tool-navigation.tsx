import type {
  NavigationEntry,
  NavigationGroup,
  NavigationTool,
} from "@/tools/registry"
export type { NavigationEntry, NavigationGroup, NavigationTool }

import {
  Building2,
  ClipboardList,
  FilePlus2,
  FolderKanban,
  Home,
  ListTodo,
  Settings,
  SlidersHorizontal,
  Target,
  Users,
  UsersRound,
} from "lucide-react"
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
    title: "nav.dashboard",
    path: "/",
  },
  {
    kind: "group",
    icon: Target,
    title: "nav.okrOverview",
    path: "/okr",
    requiresSuperuser: true,
    children: [
      {
        kind: "tool",
        icon: FolderKanban,
        title: "nav.departmentBoard",
        path: "/okr/department-board",
        requiresSuperuser: true,
      },
      {
        kind: "tool",
        icon: UsersRound,
        title: "nav.peopleBoard",
        path: "/okr/people-board",
        requiresSuperuser: true,
      },
    ],
  },
  {
    kind: "tool",
    icon: ListTodo,
    title: "nav.myTasks",
    path: "/okr/my",
  },
  {
    kind: "group",
    icon: ClipboardList,
    title: "nav.workReports",
    children: [
      {
        kind: "tool",
        icon: FilePlus2,
        title: "nav.fillWorkReport",
        path: "/work-reports/new",
      },
      {
        kind: "tool",
        icon: SlidersHorizontal,
        title: "nav.workReportConfig",
        path: "/work-reports/config",
        requiresSuperuser: true,
      },
    ],
  },
  {
    kind: "tool",
    icon: Building2,
    title: "nav.departments",
    path: "/okr/departments",
    requiresSuperuser: true,
  },
  {
    kind: "tool",
    icon: Settings,
    title: "nav.settings",
    path: "/settings",
  },
  {
    kind: "tool",
    icon: Users,
    title: "nav.users",
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
    if (entry.requiresSuperuser && !context.isSuperuser) {
      continue
    }
    if (entry.kind === "group") {
      // 组内子项也按权限过滤；过滤后为空则不显示该组
      const children = entry.children.filter(
        (child) => !child.requiresSuperuser || context.isSuperuser,
      )
      if (children.length > 0) {
        entries.push({ ...entry, children })
      }
      continue
    }
    entries.push(entry)
  }

  // Add tool entries from registry (e.g. notification if it registers navigation)
  const toolEntries = toolRegistry.getNavigationEntries(context)
  entries.push(...toolEntries)

  return entries
}
