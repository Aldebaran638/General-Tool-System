import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ShieldAlert, SlidersHorizontal } from "lucide-react"
import { useEffect, useState } from "react"

import { type FieldConfigPublic, WorkReportsService } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  FIELD_LABELS,
  SECTION_FIELDS,
  SECTION_LABELS,
  type SectionKey,
} from "./constants"

const WorkReportFieldConfig = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [items, setItems] = useState<FieldConfigPublic[]>([])
  const { data, isLoading } = useQuery({
    queryKey: ["work-report-field-config"],
    queryFn: WorkReportsService.readFieldConfig,
    enabled: Boolean(user?.is_superuser),
  })

  useEffect(() => {
    if (data?.data) setItems(data.data)
  }, [data])

  const mutation = useMutation({
    mutationFn: () =>
      WorkReportsService.updateFieldConfig({
        requestBody: {
          data: items.map(({ section, field_key, is_required }) => ({
            section,
            field_key,
            is_required,
          })),
        },
      }),
    onSuccess: (result) => {
      setItems(result.data)
      queryClient.setQueryData(["work-report-field-config"], result)
      showSuccessToast("字段规则已保存")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (user && !user.is_superuser) {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="h-4 w-4" />
        <AlertTitle>无权访问</AlertTitle>
        <AlertDescription>仅超级管理员可以修改字段规则。</AlertDescription>
      </Alert>
    )
  }

  const requiredFor = (section: string, field: string) =>
    items.find((item) => item.section === section && item.field_key === field)
      ?.is_required ?? false

  const toggle = (section: string, field: string, checked: boolean) => {
    setItems((current) =>
      current.map((item) =>
        item.section === section && item.field_key === field
          ? { ...item, is_required: checked }
          : item,
      ),
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <SlidersHorizontal className="h-6 w-6 text-primary" />
          工作汇报字段配置
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          规则全局生效，员工下一次提交时将按最新配置校验。
        </p>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">正在加载配置…</p>
      ) : null}

      {(Object.keys(SECTION_FIELDS) as SectionKey[]).map((section) => (
        <Card key={section}>
          <CardHeader>
            <CardTitle>{SECTION_LABELS[section]}</CardTitle>
            <CardDescription>设置该区域各列是否必须填写。</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {SECTION_FIELDS[section].map((field) => {
              const isConditionalReason =
                section === "task_summary" && field === "incomplete_reason"
              return (
                <div
                  key={field}
                  className="flex cursor-pointer items-start gap-3 rounded-lg border p-4"
                >
                  <Checkbox
                    checked={requiredFor(section, field)}
                    onCheckedChange={(checked) =>
                      toggle(section, field, checked === true)
                    }
                    aria-label={`${FIELD_LABELS[field]}必填`}
                  />
                  <span className="space-y-1">
                    <span className="flex items-center gap-2 font-medium">
                      {FIELD_LABELS[field]}
                      {requiredFor(section, field) ? (
                        <Badge variant="secondary">必填</Badge>
                      ) : null}
                    </span>
                    {isConditionalReason ? (
                      <span className="block text-xs text-muted-foreground">
                        即使设为可空，进度低于 100% 时仍然必填。
                      </span>
                    ) : null}
                  </span>
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}

      <LoadingButton
        loading={mutation.isPending}
        disabled={items.length === 0}
        onClick={() => mutation.mutate()}
      >
        保存配置
      </LoadingButton>
    </div>
  )
}

export default WorkReportFieldConfig
