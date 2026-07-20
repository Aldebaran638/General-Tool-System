import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { AlertCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
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
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

const formSchema = z.object({
  username: z.email(),
  password: z
    .string()
    .min(1, { message: "Password is required" })
    .min(8, { message: "Password must be at least 8 characters" }),
}) satisfies z.ZodType<AccessToken>

type FormData = z.infer<typeof formSchema>
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
        title: "Log In - 项目管理面板",
      },
    ],
  }),
})

function Login() {
  const { loginMutation } = useAuth()
  const [showSessionExpiredNotice, setShowSessionExpiredNotice] =
    useState(false)
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

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
  const submitLogin = form.handleSubmit(onSubmit)

  return (
    <AuthLayout>
      <Form {...form}>
        <form onSubmit={submitLogin} noValidate className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="title-with-line text-heading text-[#2A2A2A]">欢迎回来</h1>
            <p className="text-sm font-light text-muted-foreground">
              登录您的账户以继续
            </p>
          </div>

          {showSessionExpiredNotice ? (
            <Alert
              variant="destructive"
              className="animate-in fade-in-50 slide-in-from-top-2"
            >
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>登录已过期</AlertTitle>
              <AlertDescription>当前登录已经过期，请重新登录</AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱地址</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="请输入邮箱地址"
                      type="email"
                      className="h-11 bg-transparent transition-all"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center">
                    <FormLabel>密码</FormLabel>
                    <RouterLink
                      to="/recover-password"
                      className="ml-auto text-sm text-primary hover:text-primary/80 transition-colors"
                    >
                      忘记密码?
                    </RouterLink>
                  </div>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder="请输入密码"
                      className="h-11 bg-transparent transition-all"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
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
              登录
            </LoadingButton>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            还没有账户?{" "}
            <RouterLink
              to="/signup"
              className="font-medium text-primary hover:text-primary/80 transition-colors"
            >
              立即注册
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
