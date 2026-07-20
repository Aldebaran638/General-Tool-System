import { useMutation } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"

import { OkrService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteKrProps {
  id: string
  title: string
  /** 删除成功后回调（父组件负责退场动画与列表缓存更新） */
  onDeleted?: () => void
}

const DeleteKr = ({ id, title, onDeleted }: DeleteKrProps) => {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { handleSubmit } = useForm()

  const mutation = useMutation({
    mutationFn: () => OkrService.deleteKeyResult({ krId: id }),
    onSuccess: () => {
      showSuccessToast(t("okr.delete.krDeleted", "KR 已删除"))
      setIsOpen(false)
      onDeleted?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = async () => {
    mutation.mutate()
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive"
          aria-label={t("okr.delete.deleteKr", "删除 KR")}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>{t("okr.delete.deleteKr", "删除 KR")}</DialogTitle>
            <DialogDescription>
              {t(
                "okr.delete.krConfirm",
                "确定要删除关键结果「{{title}}」吗？此操作无法撤销。",
                { title },
              )}
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                {t("okr.delete.cancel", "取消")}
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={mutation.isPending}
            >
              {t("okr.delete.confirm", "删除")}
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteKr
