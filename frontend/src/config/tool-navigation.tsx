import type {
  NavigationEntry,
  NavigationGroup,
  NavigationTool,
} from "@/tools/registry"
export type { NavigationEntry, NavigationGroup, NavigationTool }

import { toolRegistry } from "@/tools/registry"

// Import all tool modules to trigger their self-registration
// This is the ONLY place where tool modules should be explicitly imported.
// All other navigation/route config should come from the registry.
import "@/tools/workbench/project_management"

export function getNavigationEntries(
  currentUser?: {
    is_superuser?: boolean
  } | null,
): NavigationEntry[] {
  const context = {
    isSuperuser: currentUser?.is_superuser ?? false,
  }

  return toolRegistry.getNavigationEntries(context)
}
