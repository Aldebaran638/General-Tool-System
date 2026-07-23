import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import { LoaderCircle } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { z } from "zod"
import { LoginService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { Button } from "@/components/ui/button"
import i18n from "@/i18n"

const searchSchema = z.object({
  ticket: z.string().catch(""),
  error: z.string().catch(""),
})

export const Route = createFileRoute("/login_/feishu/callback")({
  component: FeishuLoginCallback,
  validateSearch: searchSchema,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("auth.feishuLogin")} - ${i18n.t("app.name")}`,
      },
    ],
  }),
})

function FeishuLoginCallback() {
  const { t } = useTranslation()
  const { ticket, error } = Route.useSearch()
  const exchangeStarted = useRef(false)
  const [failed, setFailed] = useState(Boolean(error || !ticket))

  useEffect(() => {
    if (!ticket || error || exchangeStarted.current) return
    exchangeStarted.current = true

    LoginService.exchangeFeishuLoginTicket({ requestBody: { ticket } })
      .then((response) => {
        localStorage.setItem("access_token", response.access_token)
        window.location.replace("/")
      })
      .catch(() => setFailed(true))
  }, [error, ticket])

  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-6 text-center">
        {failed ? (
          <>
            <h1 className="title-with-line text-heading text-foreground">
              {t("auth.feishuLoginFailed")}
            </h1>
            <Button asChild variant="outline" className="h-11">
              <RouterLink to="/login">{t("auth.backToLogin")}</RouterLink>
            </Button>
          </>
        ) : (
          <>
            <LoaderCircle className="h-8 w-8 animate-spin text-primary" />
            <h1 className="title-with-line text-heading text-foreground">
              {t("auth.feishuLoggingIn")}
            </h1>
          </>
        )}
      </div>
    </AuthLayout>
  )
}
