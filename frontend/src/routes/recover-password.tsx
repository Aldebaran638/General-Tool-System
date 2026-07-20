import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"
import { LoginService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import {
  toastFirstFormError,
  useFormErrorToast,
} from "@/hooks/useFormErrorToast"
import i18n from "@/i18n"
import { handleError } from "@/utils"

export const Route = createFileRoute("/recover-password")({
  component: RecoverPassword,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: `${i18n.t("auth.passwordRecovery")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function RecoverPassword() {
  const { t } = useTranslation()
  const form = useForm<{ email: string }>({
    resolver: zodResolver(
      z.object({
        email: z.email({ message: t("errors.invalidEmail") }),
      }),
    ),
    defaultValues: {
      email: "",
    },
  })
  const { showSuccessToast, showErrorToast } = useCustomToast()
  useFormErrorToast(form.formState.errors)

  const recoverPassword = async (data: { email: string }) => {
    await LoginService.recoverPassword({
      email: data.email,
    })
  }

  const mutation = useMutation({
    mutationFn: recoverPassword,
    onSuccess: () => {
      showSuccessToast(t("auth.passwordRecoveryEmailSent"))
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = async (data: { email: string }) => {
    if (mutation.isPending) return
    mutation.mutate(data)
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit, toastFirstFormError)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="title-with-line text-heading text-foreground">
              {t("auth.passwordRecovery")}
            </h1>
            <p className="text-sm font-light text-muted-foreground">
              {t("auth.passwordRecoveryDescription")}
            </p>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("auth.email")}</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder={t("auth.emailPlaceholder")}
                      type="email"
                      {...field}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              className="w-full"
              loading={mutation.isPending}
            >
              {t("auth.continue")}
            </LoadingButton>
          </div>

          <div className="text-center text-sm">
            {t("auth.rememberPassword")}{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              {t("auth.login")}
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
