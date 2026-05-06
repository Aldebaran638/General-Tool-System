import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { ApiError, OpenAPI } from "./client"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import { I18nProvider } from "./i18n"
import "./index.css"
import { routeTree } from "./routeTree.gen"

const SESSION_EXPIRED_NOTICE_KEY = "session_expired_notice"

OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || ""
}

// Centralize auth-expiration handling so every API consumer gets the same
// logout + redirect behavior without duplicating checks in pages or hooks.
const handleApiError = (error: Error) => {
  if (!(error instanceof ApiError)) {
    return
  }

  const isExpiredSession =
    error.status === 401 ||
    (error.status === 403 &&
      (error.body as { detail?: string } | undefined)?.detail ===
        "Could not validate credentials") ||
    (error.status === 404 &&
      (error.body as { detail?: string } | undefined)?.detail === "User not found")

  if (isExpiredSession) {
    localStorage.removeItem("access_token")
    sessionStorage.setItem(SESSION_EXPIRED_NOTICE_KEY, "1")
    window.location.href = "/login"
  }
}
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <I18nProvider>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
          <Toaster richColors closeButton />
        </QueryClientProvider>
      </I18nProvider>
    </ThemeProvider>
  </StrictMode>,
)
