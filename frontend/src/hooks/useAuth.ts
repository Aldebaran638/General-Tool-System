import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"
import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
  type UserUpdateMe,
} from "@/client"
import i18n from "@/i18n"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const SUPPORTED_LANGUAGES = ["zh", "en"]

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  useEffect(() => {
    if (user?.language && SUPPORTED_LANGUAGES.includes(user.language)) {
      i18n.changeLanguage(user.language)
    }
  }, [user?.language])

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
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: async () => {
      const selectedLanguage = SUPPORTED_LANGUAGES.includes(i18n.language)
        ? i18n.language
        : "zh"

      try {
        const data: UserUpdateMe = { language: selectedLanguage }
        await UsersService.updateUserMe({ requestBody: data })
      } catch {
        // Non-blocking: language sync failure shouldn't prevent login.
      }

      const currentUser = await UsersService.readUserMe()
      if (
        currentUser.language &&
        SUPPORTED_LANGUAGES.includes(currentUser.language)
      ) {
        i18n.changeLanguage(currentUser.language)
      }
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
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
  }
}

export { isLoggedIn }
export default useAuth
