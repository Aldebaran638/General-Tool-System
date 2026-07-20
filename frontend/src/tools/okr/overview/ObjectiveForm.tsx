import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"

import type { ObjectivePublic } from "@/client"
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import {
  toastFirstFormError,
  useFormErrorToast,
} from "@/hooks/useFormErrorToast"
import { handleError } from "@/utils"

interface ObjectiveFormProps {
  /** 传入则为编辑模式，否则为新建 */
  objective?: ObjectivePublic
  trigger: React.ReactNode
}

const ObjectiveForm = ({ objective, trigger }: ObjectiveFormProps) => {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = !!objective

  const formSchema = z.object({
    title: z
      .string()
      .min(1, { message: t("okr.form.titleRequired", "请输入目标名称") })
      .max(255, {
        message: t("okr.form.titleTooLong", "目标名称不能超过 255 个字符"),
      }),
    description: z.string().optional(),
  })

  type FormData = z.infer<typeof formSchema>

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: objective?.title ?? "",
      description: objective?.description ?? "",
    },
  })
  useFormErrorToast(form.formState.errors)

  // 每次打开对话框时重置为当前 objective 的值
  const { reset } = form
  useEffect(() => {
    if (isOpen) {
      reset({
        title: objective?.title ?? "",
        description: objective?.description ?? "",
      })
    }
  }, [isOpen, objective, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      isEdit
        ? OkrService.updateObjective({
            objectiveId: objective.id,
            requestBody: {
              title: data.title,
              description: data.description || null,
            },
          })
        : OkrService.createObjective({
            requestBody: {
              title: data.title,
              description: data.description || null,
            },
          }),
    onSuccess: () => {
      showSuccessToast(
        isEdit
          ? t("okr.form.objectiveUpdated", "目标已更新")
          : t("okr.form.objectiveCreated", "目标已创建"),
      )
      form.reset()
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["objectives"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }
  const submitForm = form.handleSubmit(onSubmit, toastFirstFormError)

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit
              ? t("okr.form.editObjective", "编辑目标")
              : t("okr.form.newObjective", "新建目标")}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? t("okr.form.editObjectiveDesc", "修改该目标的名称与描述。")
              : t(
                  "okr.form.newObjectiveDesc",
                  "创建一个新的 OKR 目标，随后可为其添加关键结果。",
                )}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={submitForm} noValidate>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {t("okr.form.title", "名称")}{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("okr.form.titlePlaceholder", "目标名称")}
                        type="text"
                        {...field}
                        required
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("okr.form.description", "描述")}</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder={t(
                          "okr.form.descriptionPlaceholder",
                          "目标描述（可选）",
                        )}
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  {t("okr.form.cancel", "取消")}
                </Button>
              </DialogClose>
              <LoadingButton
                type="button"
                loading={mutation.isPending}
                onClick={submitForm}
              >
                {t("okr.form.save", "保存")}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default ObjectiveForm
