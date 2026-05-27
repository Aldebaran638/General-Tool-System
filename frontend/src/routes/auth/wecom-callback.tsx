/**
 * WeCom OAuth Callback Page  (/auth/wecom/callback)
 *
 * WeCom OAuth flow backend redirects here with:
 *   /auth/wecom/callback?token=<jwt>
 *
 * This page:
 *   1. Reads the token from the query string.
 *   2. Stores it in localStorage (same key the rest of the app uses).
 *   3. Navigates to the main layout ("/").
 *
 * On error (missing token), redirects to /login.
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"
import { z } from "zod"

const searchSchema = z.object({
  token: z.string().optional(),
})

export const Route = createFileRoute("/auth/wecom-callback")({
  validateSearch: searchSchema,
  component: WecomCallback,
  head: () => ({
    meta: [{ title: "正在登录..." }],
  }),
})

function WecomCallback() {
  const { token } = Route.useSearch()
  const navigate = useNavigate()

  useEffect(() => {
    if (token) {
      localStorage.setItem("access_token", token)
      navigate({ to: "/", replace: true })
    } else {
      navigate({ to: "/login", replace: true })
    }
  }, [token, navigate])

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-2">
        <div className="text-base font-medium">正在登录...</div>
        <div className="text-sm text-muted-foreground">请稍候</div>
      </div>
    </div>
  )
}
