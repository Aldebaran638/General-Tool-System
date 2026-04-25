import type { LucideIcon } from "lucide-react"
import type { ComponentType } from "react"

// =============================================================================
// Tool Registry Types
// =============================================================================

export type ToolRouteConfig = {
  /** Route path, e.g., "/items" */
  path: string
  /** Page title */
  title: string
  /** React component to render */
  component: ComponentType
}

export type ToolNavigationConfig = {
  /** Display title in sidebar */
  title: string
  /** Lucide icon */
  icon: LucideIcon
  /** Route path */
  path: string
  /** Whether this tool requires superuser */
  requiresSuperuser?: boolean
}

export type ToolModuleConfig = {
  /** Unique tool identifier */
  name: string
  /** Group name, e.g., "workbench" */
  group: string
  /** Route configuration */
  route: ToolRouteConfig
  /** Navigation configuration */
  navigation: ToolNavigationConfig
}

// =============================================================================
// Tool Registry
// =============================================================================

class ToolRegistry {
  private tools: Map<string, ToolModuleConfig> = new Map()
  private groups: Map<string, string[]> = new Map()

  register(config: ToolModuleConfig): void {
    if (this.tools.has(config.name)) {
      throw new Error(`Tool "${config.name}" is already registered`)
    }

    this.tools.set(config.name, config)

    if (!this.groups.has(config.group)) {
      this.groups.set(config.group, [])
    }
    this.groups.get(config.group)!.push(config.name)
  }

  getTool(name: string): ToolModuleConfig | undefined {
    return this.tools.get(name)
  }

  getAllTools(): ToolModuleConfig[] {
    return Array.from(this.tools.values())
  }

  getToolsByGroup(group: string): ToolModuleConfig[] {
    const names = this.groups.get(group) || []
    return names.map((name) => this.tools.get(name)!).filter(Boolean)
  }

  getAllGroups(): string[] {
    return Array.from(this.groups.keys())
  }

  getNavigationEntries(context: { isSuperuser: boolean }): NavigationEntry[] {
    const entries: NavigationEntry[] = []

    for (const [groupName, toolNames] of this.groups) {
      const children = toolNames
        .map((name) => this.tools.get(name)!)
        .filter((tool) => {
          if (tool.navigation.requiresSuperuser && !context.isSuperuser) {
            return false
          }
          return true
        })
        .map((tool) => ({
          kind: "tool" as const,
          icon: tool.navigation.icon,
          title: tool.navigation.title,
          path: tool.navigation.path,
          requiresSuperuser: tool.navigation.requiresSuperuser,
        }))

      if (children.length > 0) {
        entries.push({
          kind: "group",
          icon: children[0].icon, // Use first child's icon as group icon
          title: this._formatGroupName(groupName),
          children,
          defaultExpanded: true,
        })
      }
    }

    return entries
  }

  private _groupNameMap: Record<string, string> = {
    finance: "财务",
  }

  private _formatGroupName(name: string): string {
    if (this._groupNameMap[name]) {
      return this._groupNameMap[name]
    }
    return name
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }
}

// =============================================================================
// Navigation Types (for backward compatibility with tool-navigation.tsx)
// =============================================================================

export type NavigationTool = {
  kind: "tool"
  icon: LucideIcon
  title: string
  path: string
  requiresSuperuser?: boolean
}

export type NavigationGroup = {
  kind: "group"
  icon: LucideIcon
  title: string
  children: NavigationTool[]
  defaultExpanded?: boolean
}

export type NavigationEntry = NavigationTool | NavigationGroup

// =============================================================================
// Global Registry Instance
// =============================================================================

export const toolRegistry = new ToolRegistry()

/** Convenience function to register a tool */
export function registerTool(config: ToolModuleConfig): void {
  toolRegistry.register(config)
}
