import { Globe } from "lucide-react"
import { useTranslation } from "react-i18next"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import i18n from "@/i18n"

/**
 * Language switcher for unauthenticated surfaces (auth pages).
 * Only changes the i18n locale — no backend sync, since there is no user yet.
 * The selected locale is persisted to the account on successful login.
 */
export function LanguageSwitcher() {
  const { t } = useTranslation()

  return (
    <div className="flex items-center gap-2">
      <Globe className="h-4 w-4 text-muted-foreground" />
      <Select
        value={i18n.language}
        onValueChange={(value) => i18n.changeLanguage(value)}
      >
        <SelectTrigger className="h-8 w-28 text-xs">
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
