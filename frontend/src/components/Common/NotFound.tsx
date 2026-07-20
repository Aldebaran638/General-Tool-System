import { Link, useRouter } from "@tanstack/react-router"
import { ArrowLeft, Home } from "lucide-react"
import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/button"

const NotFound = () => {
  const router = useRouter()
  const { t } = useTranslation()

  return (
    <div
      className="relative flex min-h-svh items-center justify-center flex-col bg-background p-4"
      data-testid="not-found"
    >
      <div className="flex flex-col items-center text-center max-w-md rounded-md bg-card border border-border p-8 md:p-10">
        <h1 className="text-display text-primary">404</h1>
        <h2 className="mt-4 text-heading text-foreground">
          {t("notFound.title")}
        </h2>
        <p className="mt-3 text-sm font-light text-muted-foreground">
          {t("notFound.description")}
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <Link to="/">
            <Button size="lg" className="font-normal tracking-wide">
              <Home className="mr-2 h-4 w-4" />
              {t("notFound.backHome")}
            </Button>
          </Link>
          <Button
            variant="outline"
            size="lg"
            onClick={() => router.history.back()}
            className="font-normal tracking-wide"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t("notFound.backPrevious")}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFound
