import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check } from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import type { KeyResultPublic } from "@/client"
import { OkrService } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ProgressEditorProps {
  kr: KeyResultPublic
}

const clampProgress = (value: number) =>
  Math.min(100, Math.max(0, Math.round(value)))

const ProgressEditor = ({ kr }: ProgressEditorProps) => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const serverProgress = Math.round(kr.progress ?? 0)
  const [value, setValue] = useState(serverProgress)

  // 服务端数据刷新后同步本地值
  useEffect(() => {
    setValue(serverProgress)
  }, [serverProgress])

  const dirty = value !== serverProgress

  const mutation = useMutation({
    mutationFn: (progress: number) =>
      OkrService.updateKrProgress({ krId: kr.id, requestBody: { progress } }),
    onSuccess: () => {
      showSuccessToast(t("okr.progress.saved", "进度已更新"))
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["my-krs"] })
    },
  })

  const save = () => {
    if (dirty && !mutation.isPending) {
      mutation.mutate(value)
    }
  }

  return (
    <div className="flex shrink-0 items-center gap-2">
      <Input
        type="number"
        min={0}
        max={100}
        value={value}
        onChange={(e) => {
          const next = Number(e.target.value)
          setValue(Number.isNaN(next) ? 0 : clampProgress(next))
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault()
            save()
          }
        }}
        className="h-8 w-20"
        aria-label={t("okr.progress.label", "进度")}
      />
      <span className="text-caption text-muted-foreground">%</span>
      {dirty && (
        <Button
          size="icon"
          className="h-8 w-8"
          onClick={save}
          disabled={mutation.isPending}
          aria-label={t("okr.progress.save", "保存进度")}
        >
          <Check className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}

export default ProgressEditor
