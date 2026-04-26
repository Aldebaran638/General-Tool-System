import { Globe } from "lucide-react"
import { useI18n } from "@/i18n"
import { LOCALE_LABELS, SUPPORTED_LOCALES, type Locale } from "@/i18n/locales"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"

export default function LanguageSelector() {
  const { locale, setLocale, t } = useI18n()

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Globe className="h-4 w-4 text-muted-foreground" />
        <Label htmlFor="language-select">{t("settings.languageLabel")}</Label>
      </div>
      <p className="text-sm text-muted-foreground">
        {t("settings.languageDescription")}
      </p>
      <Select
        value={locale}
        onValueChange={(value) => setLocale(value as Locale)}
      >
        <SelectTrigger id="language-select" className="w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SUPPORTED_LOCALES.map((loc: Locale) => (
            <SelectItem key={loc} value={loc}>
              {LOCALE_LABELS[loc]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
