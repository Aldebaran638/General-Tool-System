import { useQuery } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useTranslation } from "react-i18next"

import type { KeyResultPublic } from "@/client"
import { OkrService } from "@/client"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import DeleteKr from "@/tools/okr/overview/DeleteKr"
import KrForm from "@/tools/okr/overview/KrForm"

interface KrTableProps {
  objectiveId: string
  /** 卡片展开时才拉取数据 */
  enabled: boolean
}

const KrTable = ({ objectiveId, enabled }: KrTableProps) => {
  const { t } = useTranslation()

  const { data, isPending } = useQuery({
    queryKey: ["objective-krs", objectiveId],
    queryFn: () => OkrService.readObjectiveKrs({ objectiveId }),
    enabled,
  })

  // 收起时保持内容挂载（数据已缓存），grid-rows 收起动画才不会跳动
  if (isPending) {
    return (
      <div className="flex flex-col gap-2 py-2">
        {Array.from({ length: 2 }).map((_, index) => (
          <Skeleton key={index} className="h-8 w-full" />
        ))}
      </div>
    )
  }

  const krs = data?.data ?? []

  if (krs.length === 0) {
    return (
      <p className="py-4 text-center text-caption text-muted-foreground">
        {t("okr.krTable.empty", "暂无 KR，点击右上角「添加 KR」创建。")}
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("okr.krTable.name", "名称")}</TableHead>
          <TableHead>{t("okr.krTable.description", "详情")}</TableHead>
          <TableHead>{t("okr.krTable.department", "部门")}</TableHead>
          <TableHead>{t("okr.krTable.assignee", "人员")}</TableHead>
          <TableHead>{t("okr.krTable.startDate", "开始时间")}</TableHead>
          <TableHead>{t("okr.krTable.deadline", "DDL")}</TableHead>
          <TableHead className="w-40">
            {t("okr.krTable.progress", "进度")}
          </TableHead>
          <TableHead>
            <span className="sr-only">{t("okr.krTable.actions", "操作")}</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {krs.map((kr: KeyResultPublic) => (
          <TableRow key={kr.id}>
            <TableCell className="max-w-48">
              <span className="block truncate font-medium" title={kr.title}>
                {kr.title}
              </span>
            </TableCell>
            <TableCell className="max-w-56">
              <span
                className="block truncate text-muted-foreground"
                title={kr.description ?? undefined}
              >
                {kr.description || "—"}
              </span>
            </TableCell>
            <TableCell>{kr.department?.name ?? "—"}</TableCell>
            <TableCell>{kr.assignee.full_name || kr.assignee.email}</TableCell>
            <TableCell className="whitespace-nowrap">
              {kr.start_date.slice(0, 10)}
            </TableCell>
            <TableCell className="whitespace-nowrap">
              {kr.deadline.slice(0, 10)}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <Progress value={kr.progress ?? 0} className="h-2 flex-1" />
                <span className="w-10 shrink-0 text-right text-caption text-muted-foreground">
                  {Math.round(kr.progress ?? 0)}%
                </span>
              </div>
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <KrForm
                  objectiveId={objectiveId}
                  kr={kr}
                  trigger={
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground"
                      aria-label={t("okr.krTable.edit", "编辑 KR")}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  }
                />
                <DeleteKr
                  id={kr.id}
                  objectiveId={objectiveId}
                  title={kr.title}
                />
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export default KrTable
