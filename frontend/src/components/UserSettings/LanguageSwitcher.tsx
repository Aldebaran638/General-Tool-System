import { useMutation, useQueryClient } from "@tanstack/react-query"
import i18n from "i18next"
import { Globe } from "lucide-react"
import { useTranslation } from "react-i18next"

import { UsersService, type UserUpdateMe } from "@/client"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function LanguageSwitcher() {
  const { t } = useTranslation()
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (language: string) => {
      const data: UserUpdateMe = { language }
      return UsersService.updateUserMe({ requestBody: data })
    },
    onSuccess: () => {
      showSuccessToast(t("profile.updated"))
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    },
  })

  const handleChange = (value: string) => {
    i18n.changeLanguage(value)
    mutation.mutate(value)
  }

  return (
    <div className="flex items-center gap-3">
      <Globe className="h-4 w-4 text-muted-foreground" />
      <span className="text-sm font-medium">{t("settings.language")}</span>
      <Select
        value={currentUser?.language || i18n.language}
        onValueChange={handleChange}
        disabled={mutation.isPending}
      >
        <SelectTrigger className="w-32">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="zh">{t("settings.chinese")}</SelectItem>
          <SelectItem value="en">{t("settings.english")}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
