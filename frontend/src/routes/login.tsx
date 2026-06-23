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
import useAuth, { isLoggedIn, redirectToWecomOAuth } from "@/hooks/useAuth"

const formSchema = z.object({
  username: z.string().min(1, { message: "企微账号不能为空" }),
  password: z
    .string()
    .min(1, { message: "Password is required" }),
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
        title: "Log In - 通用工具系统",
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
            <div className="lg:hidden rounded-full bg-primary/10 p-3 mb-2">
              <svg
                className="h-8 w-8 text-primary"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 14l9-5-9-5-9 5 9 5z" />
                <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">欢迎回来</h1>
            <p className="text-sm text-muted-foreground">
              登录您的账户以继续学习
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
                  <FormLabel>企微账号</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="请输入企微账号"
                      type="text"
                      className="h-11 transition-all focus-visible:ring-2 focus-visible:ring-primary/20"
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
                      className="h-11 transition-all focus-visible:ring-2 focus-visible:ring-primary/20"
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
              className="h-11 font-medium transition-all hover:shadow-md"
            >
              登录
            </LoadingButton>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                或者
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={redirectToWecomOAuth}
            className="group flex w-full items-center justify-center gap-3 rounded-lg border border-input bg-background px-4 py-3 text-sm font-medium shadow-sm transition-all hover:bg-accent hover:text-accent-foreground hover:shadow-md hover:border-primary/20"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5 transition-transform group-hover:scale-110"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M9.5 13.5a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm5 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" />
              <path
                fillRule="evenodd"
                d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2Zm-4.5 7a4.5 4.5 0 1 0 9 0 4.5 4.5 0 0 0-9 0Z"
                clipRule="evenodd"
              />
            </svg>
            企业微信一键登录
          </button>

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
