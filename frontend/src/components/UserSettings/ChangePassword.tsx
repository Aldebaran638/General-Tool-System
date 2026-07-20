import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"
import { Lock, KeyRound, ShieldCheck } from "lucide-react"

import { type UpdatePassword, UsersService } from "@/client"
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
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const ChangePassword = () => {
  const { t } = useTranslation()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const formSchema = z
    .object({
      current_password: z
        .string()
        .min(1, { message: t("errors.required") })
        .min(8, { message: t("errors.passwordMin", { count: 8 }) }),
      new_password: z
        .string()
        .min(1, { message: t("errors.required") })
        .min(8, { message: t("errors.passwordMin", { count: 8 }) }),
      confirm_password: z.string().min(1, { message: t("errors.required") }),
    })
    .refine((data) => data.new_password === data.confirm_password, {
      message: t("errors.passwordMatch"),
      path: ["confirm_password"],
    })

  type FormData = z.infer<typeof formSchema>

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onSubmit",
    criteriaMode: "all",
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: UpdatePassword) =>
      UsersService.updatePasswordMe({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast(t("password.updated"))
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = async (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-primary" />
          {t("password.title")}
        </CardTitle>
        <CardDescription>{t("password.description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-5"
          >
            <FormField
              control={form.control}
              name="current_password"
              render={({ field, fieldState }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-1.5">
                    <KeyRound className="h-3.5 w-3.5 text-muted-foreground" />
                    {t("password.current")}
                  </FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="current-password-input"
                      placeholder={t("password.current")}
                      aria-invalid={fieldState.invalid}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="new_password"
              render={({ field, fieldState }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
                    {t("password.new")}
                  </FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="new-password-input"
                      placeholder={t("password.new")}
                      aria-invalid={fieldState.invalid}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field, fieldState }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
                    {t("password.confirm")}
                  </FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="confirm-password-input"
                      placeholder={t("password.confirm")}
                      aria-invalid={fieldState.invalid}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              loading={mutation.isPending}
              className="self-start"
            >
              {t("password.update")}
            </LoadingButton>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

export default ChangePassword
