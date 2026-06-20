import { Download, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { useEquipmentPurchaseVersionsQuery, useDeleteEquipmentPurchaseVersionMutation } from "../hooks/useEquipmentPurchaseFiller"
import type { FilledVersion } from "../types"

interface VersionsTabProps {
  onLoad: (version: FilledVersion) => void
  onExport: (version: FilledVersion) => void
}

export function VersionsTab({ onLoad, onExport }: VersionsTabProps) {
  const { data: versions = [], isLoading } = useEquipmentPurchaseVersionsQuery()
  const deleteMutation = useDeleteEquipmentPurchaseVersionMutation()

  if (isLoading) {
    return <div className="p-4">加载中...</div>
  }

  if (versions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
        暂无保存的版本
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>版本名称</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {versions.map((version) => (
            <TableRow key={version.id}>
              <TableCell className="font-medium">{version.version_name}</TableCell>
              <TableCell>
                {version.created_at
                  ? new Date(version.created_at).toLocaleString("zh-CN")
                  : "-"}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onLoad(version)}
                >
                  加载
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onExport(version)}
                >
                  <Download className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => deleteMutation.mutate(version.id)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
