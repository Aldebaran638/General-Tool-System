import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { AlertCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { z } from "zod"
import type { Body_login_login_access_token as AccessToken } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import {
  toastFirstFormError,
  useFormErrorToast,
} from "@/hooks/useFormErrorToast"
import i18n from "@/i18n"

const SESSION_EXPIRED_NOTICE_KEY = "session_expired_notice"

export const Route = createFileRoute("/login")({
  component: Login,
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
        title: `${i18n.t("auth.login")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function Login() {
  const { t } = useTranslation()
  const { loginMutation } = useAuth()
  const [showSessionExpiredNotice, setShowSessionExpiredNotice] =
    useState(false)

  const formSchema = z.object({
    username: z.email({ message: t("errors.invalidEmail") }),
    password: z
      .string()
      .min(1, { message: t("errors.required") })
      .min(8, { message: t("errors.passwordMin", { count: 8 }) }),
  }) satisfies z.ZodType<AccessToken>

  type FormData = z.infer<typeof formSchema>

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })
  useFormErrorToast(form.formState.errors)

  // Consume the redirect flag once so the user sees a clear re-login notice
  // after the global request layer invalidates an expired session.
  useEffect(() => {
    const shouldShowNotice =
      sessionStorage.getItem(SESSION_EXPIRED_NOTICE_KEY) === "1"

    if (shouldShowNotice) {
      setShowSessionExpiredNotice(true)
      sessionStorage.removeItem(SESSION_EXPIRED_NOTICE_KEY)
    }
  }, [])

  const onSubmit = (data: FormData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
  }
  const submitLogin = form.handleSubmit(onSubmit, toastFirstFormError)

  return (
    <AuthLayout>
      <Form {...form}>
        <form onSubmit={submitLogin} noValidate className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="title-with-line text-heading text-foreground">
              {t("auth.welcomeBack")}
            </h1>
            <p className="text-sm font-light text-muted-foreground">
              {t("auth.loginToContinue")}
            </p>
          </div>

          {showSessionExpiredNotice ? (
            <Alert
              variant="destructive"
              className="animate-in fade-in-50 slide-in-from-top-2"
            >
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>{t("auth.sessionExpired")}</AlertTitle>
              <AlertDescription>
                {t("auth.sessionExpiredDescription")}
              </AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("auth.email")}</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder={t("auth.emailPlaceholder")}
                      type="email"
                      className="h-11 bg-transparent transition-all"
                      {...field}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center">
                    <FormLabel>{t("auth.password")}</FormLabel>
                    <RouterLink
                      to="/recover-password"
                      className="ml-auto text-sm text-primary hover:text-primary/80 transition-colors"
                    >
                      {t("auth.forgotPassword")}
                    </RouterLink>
                  </div>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder={t("auth.passwordPlaceholder")}
                      className="h-11 bg-transparent transition-all"
                      {...field}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <LoadingButton
              type="button"
              loading={loginMutation.isPending}
              onClick={submitLogin}
              data-testid="login-submit"
              className="h-11 font-normal tracking-wide transition-colors"
            >
              {t("auth.login")}
            </LoadingButton>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            {t("auth.noAccount")}{" "}
            <RouterLink
              to="/signup"
              className="font-medium text-primary hover:text-primary/80 transition-colors"
            >
              {t("auth.signUp")}
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
