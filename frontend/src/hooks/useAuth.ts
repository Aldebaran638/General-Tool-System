import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

async function fetchCurrentUserRoles(): Promise<string[]> {
  const token = localStorage.getItem("access_token")
  if (!token) return []
  const res = await fetch("/api/v1/users/me/roles", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return []
  const data = await res.json().catch(() => ({}))
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.roles)) return data.roles
  return []
}

/**
 * Returns true when the page is running inside the WeCom built-in browser.
 * WeCom injects "wxwork" into the User-Agent string on both Android and iOS.
 */
const isWecomBrowser = (): boolean => /wxwork/i.test(navigator.userAgent)

/**
 * Perform a full-page navigation to the backend WeCom OAuth entry point.
 * The backend will 302-redirect to WeCom OAuth; after authorisation WeCom
 * redirects to /api/auth/wecom/callback, which issues a JWT and sends the
 * browser to /auth/wecom/callback?token=<jwt>.
 */
const redirectToWecomOAuth = (): void => {
  window.location.href = "/api/auth/wecom/login"
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const { data: roles } = useQuery<string[], Error>({
    queryKey: ["currentUserRoles"],
    queryFn: fetchCurrentUserRoles,
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)

    // Eagerly fetch current user and roles so the dashboard/sidebar don't flash empty
    // while the useQuery for ["currentUser"] / ["currentUserRoles"] is still loading.
    const [currentUser, currentRoles] = await Promise.all([
      UsersService.readUserMe(),
      fetchCurrentUserRoles(),
    ])
    queryClient.setQueryData(["currentUser"], currentUser)
    queryClient.setQueryData(["currentUserRoles"], currentRoles)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    roles,
  }
}

export { isLoggedIn, isWecomBrowser, redirectToWecomOAuth }
export default useAuth
