import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function fetchCurrentUserRoles(): Promise<string[]> {
  const res = await fetch("/api/v1/users/me/roles", {
    headers: authHeaders(),
  })
  if (!res.ok) return []
  const data = await res.json().catch(() => ({}))
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.roles)) return data.roles
  return []
}

export const Route = createFileRoute("/_layout/question-bank-management")({
  component: () => <Outlet />,
  beforeLoad: async () => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      throw redirect({ to: "/login" })
    }
    try {
      const user = await UsersService.readUserMe()
      if (user.is_superuser) return
      const roles = await fetchCurrentUserRoles()
      if (!roles.includes("EXAM_ADMIN") && !roles.includes("SUPER_ADMIN")) {
        throw redirect({ to: "/" })
      }
    } catch (error) {
      // If the user session is invalid, redirect to login instead of crashing.
      throw redirect({ to: "/login" })
    }
  },
})
