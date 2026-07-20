import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"

import type { KeyResultPublic } from "@/client"
import { OkrService, UsersService } from "@/client"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import {
  toastFirstFormError,
  useFormErrorToast,
} from "@/hooks/useFormErrorToast"
import { handleError } from "@/utils"

interface KrFormProps {
  objectiveId: string
  /** 传入则为编辑模式，否则为新建 */
  kr?: KeyResultPublic
  trigger: React.ReactNode
}

const KrForm = ({ objectiveId, kr, trigger }: KrFormProps) => {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = !!kr

  const { data: usersData } = useQuery({
    queryKey: ["users"],
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 100 }),
  })
  const { data: departmentsData } = useQuery({
    queryKey: ["departments"],
    queryFn: () => OkrService.readDepartments(),
  })
  const users = usersData?.data ?? []
  const departmentNameById = new Map(
    (departmentsData?.data ?? []).map((d) => [d.id, d.name]),
  )

  const formSchema = z
    .object({
      title: z
        .string()
        .min(1, { message: t("okr.krForm.titleRequired", "请输入 KR 名称") })
        .max(255, {
          message: t("okr.krForm.titleTooLong", "KR 名称不能超过 255 个字符"),
        }),
      description: z.string().optional(),
      assignee_id: z
        .string()
        .min(1, { message: t("okr.krForm.assigneeRequired", "请选择负责人") }),
      start_date: z
        .string()
        .min(1, { message: t("okr.krForm.startRequired", "请选择开始时间") }),
      deadline: z.string().min(1, {
        message: t("okr.krForm.deadlineRequired", "请选择截止时间"),
      }),
      progress: z
        .number({
          message: t("okr.krForm.progressRange", "进度需在 0-100 之间"),
        })
        .min(0, {
          message: t("okr.krForm.progressRange", "进度需在 0-100 之间"),
        })
        .max(100, {
          message: t("okr.krForm.progressRange", "进度需在 0-100 之间"),
        }),
    })
    .refine(
      (data) =>
        !data.start_date || !data.deadline || data.deadline >= data.start_date,
      {
        message: t(
          "okr.krForm.deadlineBeforeStart",
          "截止时间不能早于开始时间",
        ),
        path: ["deadline"],
      },
    )

  type FormData = z.infer<typeof formSchema>

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: kr?.title ?? "",
      description: kr?.description ?? "",
      assignee_id: kr?.assignee.id ?? "",
      start_date: kr?.start_date?.slice(0, 10) ?? "",
      deadline: kr?.deadline?.slice(0, 10) ?? "",
      progress: kr?.progress ?? 0,
    },
  })
  useFormErrorToast(form.formState.errors)

  // 每次打开对话框时重置为当前 KR 的值
  const { reset } = form
  useEffect(() => {
    if (isOpen) {
      reset({
        title: kr?.title ?? "",
        description: kr?.description ?? "",
        assignee_id: kr?.assignee.id ?? "",
        start_date: kr?.start_date?.slice(0, 10) ?? "",
        deadline: kr?.deadline?.slice(0, 10) ?? "",
        progress: kr?.progress ?? 0,
      })
    }
  }, [isOpen, kr, reset])

  const assigneeId = form.watch("assignee_id")
  const selectedUser = users.find((u) => u.id === assigneeId)
  const selectedDepartmentName = selectedUser?.department_id
    ? departmentNameById.get(selectedUser.department_id)
    : undefined

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      isEdit
        ? OkrService.updateKeyResult({
            krId: kr.id,
            requestBody: {
              title: data.title,
              description: data.description || null,
              assignee_id: data.assignee_id,
              start_date: data.start_date,
              deadline: data.deadline,
              progress: data.progress,
            },
          })
        : OkrService.createKeyResult({
            requestBody: {
              title: data.title,
              description: data.description || null,
              assignee_id: data.assignee_id,
              start_date: data.start_date,
              deadline: data.deadline,
              progress: data.progress,
              objective_id: objectiveId,
            },
          }),
    onSuccess: () => {
      showSuccessToast(
        isEdit
          ? t("okr.krForm.krUpdated", "KR 已更新")
          : t("okr.krForm.krCreated", "KR 已创建"),
      )
      form.reset()
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["objective-krs", objectiveId],
      })
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
              ? t("okr.krForm.editKr", "编辑 KR")
              : t("okr.krForm.newKr", "新建 KR")}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? t("okr.krForm.editKrDesc", "修改该关键结果的各项信息。")
              : t("okr.krForm.newKrDesc", "为该目标添加一个关键结果。")}
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
                      {t("okr.krForm.title", "名称")}{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t(
                          "okr.krForm.titlePlaceholder",
                          "KR 名称",
                        )}
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
                    <FormLabel>{t("okr.krForm.description", "详情")}</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder={t(
                          "okr.krForm.descriptionPlaceholder",
                          "KR 详情（可选）",
                        )}
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="assignee_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {t("okr.krForm.assignee", "人员")}{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={t(
                              "okr.krForm.assigneePlaceholder",
                              "选择负责人",
                            )}
                          />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id}>
                            {user.full_name || user.email}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedUser && (
                      <p className="text-caption text-muted-foreground">
                        {t("okr.krForm.department", "部门")}:{" "}
                        {selectedDepartmentName ??
                          t("okr.krForm.noDepartment", "未分配")}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="start_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        {t("okr.krForm.startDate", "开始时间")}{" "}
                        <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input type="date" {...field} required />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="deadline"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        {t("okr.krForm.deadline", "DDL")}{" "}
                        <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input type="date" {...field} required />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="progress"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("okr.krForm.progress", "进度")}</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        {...field}
                        onChange={(e) => field.onChange(e.target.valueAsNumber)}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  {t("okr.krForm.cancel", "取消")}
                </Button>
              </DialogClose>
              <LoadingButton
                type="button"
                loading={mutation.isPending}
                onClick={submitForm}
              >
                {t("okr.krForm.save", "保存")}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default KrForm
