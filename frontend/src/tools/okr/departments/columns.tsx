import type { ColumnDef } from "@tanstack/react-table"
import type { TFunction } from "i18next"

import type { DepartmentPublic } from "@/client"
import i18n from "@/i18n"
import { DepartmentActionsMenu } from "./DepartmentActionsMenu"

interface DepartmentColumnActions {
  onMoveUp: (index: number) => void
  onMoveDown: (index: number) => void
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat(i18n.language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date)
}

export function getColumns(
  t: TFunction,
  actions: DepartmentColumnActions,
): ColumnDef<DepartmentPublic>[] {
  return [
    {
      accessorKey: "name",
      header: t("okr.department.name"),
      cell: ({ row }) => (
        <span className="font-medium">{row.original.name}</span>
      ),
    },
    {
      accessorKey: "description",
      header: t("okr.department.description"),
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.description || "—"}
        </span>
      ),
    },
    {
      accessorKey: "sort_order",
      header: t("okr.department.sortOrder"),
      cell: ({ row }) => (
        <span className="text-muted-foreground">{row.original.sort_order}</span>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("okr.department.createdAt"),
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {formatDate(row.original.created_at)}
        </span>
      ),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("okr.common.actions")}</span>,
      cell: ({ row, table }) => (
        <div className="flex justify-end">
          <DepartmentActionsMenu
            department={row.original}
            index={row.index}
            total={table.getCoreRowModel().rows.length}
            onMoveUp={actions.onMoveUp}
            onMoveDown={actions.onMoveDown}
          />
        </div>
      ),
    },
  ]
}
