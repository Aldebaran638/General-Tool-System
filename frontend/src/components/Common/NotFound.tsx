import { Link, useRouter } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { Home, ArrowLeft } from "lucide-react"

const NotFound = () => {
  const router = useRouter()

  return (
    <div
      className="relative flex min-h-svh items-center justify-center flex-col p-4 overflow-hidden"
      data-testid="not-found"
    >
      {/* Background gradient matching login page */}
      <div className="absolute inset-0 bg-gradient-to-br from-teal-600 via-teal-800 to-emerald-950 dark:from-teal-900 dark:via-teal-950 dark:to-emerald-950" />

      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-emerald-400/15 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-60 w-60 rounded-full bg-teal-300/10 blur-2xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center max-w-md">
        {/* Logo */}
        <div className="rounded-2xl bg-white/90 p-4 backdrop-blur-md border border-white/40 shadow-lg shadow-black/10 mb-8">
          <img
            src="/assets/images/company-logo.png"
            alt="WINKEY"
            className="h-12 w-auto"
          />
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-6xl font-bold text-white mb-2">
          404
        </h1>
        <h2 className="text-2xl font-bold text-white mb-3">
          页面走丢了
        </h2>
        <p className="text-teal-100 mb-8">
          您访问的页面不存在或已被移除
        </p>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link to="/">
            <Button
              size="lg"
              className="bg-white text-teal-800 hover:bg-white/90 shadow-lg"
            >
              <Home className="mr-2 h-4 w-4" />
              返回首页
            </Button>
          </Link>
          <Button
            variant="outline"
            size="lg"
            onClick={() => router.history.back()}
            className="border-white/30 text-white hover:bg-white/10 hover:text-white"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回上一页
          </Button>
        </div>

        {/* Footer */}
        <p className="mt-12 text-sm text-teal-200/70">
          © {new Date().getFullYear()} WINKEY. All rights reserved.
        </p>
      </div>
    </div>
  )
}

export default NotFound
