import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"
import { User, Mail, Pencil, Check, X } from "lucide-react"

import { UsersService, type UserUpdateMe } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"
import { LanguageSwitcher } from "./LanguageSwitcher"

const UserInformation = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()

  const formSchema = z.object({
    full_name: z.string().max(30).optional(),
    email: z.email({ message: t("errors.invalidEmail") }),
  })

  type FormData = z.infer<typeof formSchema>

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      full_name: currentUser?.full_name ?? undefined,
      email: currentUser?.email,
    },
  })

  useEffect(() => {
    form.reset({
      full_name: currentUser?.full_name ?? "",
      email: currentUser?.email ?? "",
    })
  }, [currentUser?.email, currentUser?.full_name, form])

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      UsersService.updateUserMe({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast(t("profile.updated"))
      toggleEditMode()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  const onSubmit = (data: FormData) => {
    const updateData: UserUpdateMe = {}

    if (data.full_name !== currentUser?.full_name) {
      updateData.full_name = data.full_name
    }
    if (data.email !== currentUser?.email) {
      updateData.email = data.email
    }

    mutation.mutate(updateData)
  }

  const onCancel = () => {
    form.reset()
    toggleEditMode()
  }

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5 text-primary" />
          {t("profile.title")}
        </CardTitle>
        <CardDescription>{t("profile.description")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <LanguageSwitcher />
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-5"
          >
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) =>
                editMode ? (
                  <FormItem>
                    <FormLabel>{t("profile.name")}</FormLabel>
                    <FormControl>
                      <Input type="text" placeholder={t("auth.fullNamePlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                ) : (
                  <FormItem>
                    <FormLabel className="flex items-center gap-1.5">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      {t("profile.name")}
                    </FormLabel>
                    <div
                      className={cn(
                        "rounded-md border bg-muted/30 px-3 py-2.5 text-sm",
                        !field.value && "text-muted-foreground",
                      )}
                    >
                      {field.value || "—"}
                    </div>
                  </FormItem>
                )
              }
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) =>
                editMode ? (
                  <FormItem>
                    <FormLabel>{t("profile.email")}</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder={t("auth.emailPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                ) : (
                  <FormItem>
                    <FormLabel className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                      {t("profile.email")}
                    </FormLabel>
                    <div className="rounded-md border bg-muted/30 px-3 py-2.5 text-sm">
                      {field.value}
                    </div>
                  </FormItem>
                )
              }
            />

            <div className="flex gap-3 pt-2">
              {editMode ? (
                <>
                  <LoadingButton
                    type="submit"
                    loading={mutation.isPending}
                    disabled={!form.formState.isDirty}
                  >
                    <Check className="mr-1.5 h-4 w-4" />
                    {t("profile.save")}
                  </LoadingButton>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onCancel}
                    disabled={mutation.isPending}
                  >
                    <X className="mr-1.5 h-4 w-4" />
                    {t("profile.cancel")}
                  </Button>
                </>
              ) : (
                <Button type="button" onClick={toggleEditMode}>
                  <Pencil className="mr-1.5 h-4 w-4" />
                  {t("profile.edit")}
                </Button>
              )}
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

export default UserInformation
