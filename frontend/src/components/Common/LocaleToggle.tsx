import { Check, Globe } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useI18n } from "@/i18n"
import { LOCALE_LABELS, SUPPORTED_LOCALES, type Locale } from "@/i18n/locales"

export const LocaleToggle = () => {
  const { locale, setLocale } = useI18n()

  return (
    <div className="flex items-center justify-center">
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button data-testid="locale-button" variant="outline" size="icon">
            <Globe className="h-[1.2rem] w-[1.2rem]" />
            <span className="sr-only">Switch language</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {SUPPORTED_LOCALES.map((loc: Locale) => (
            <DropdownMenuItem
              key={loc}
              data-testid={`locale-${loc}`}
              onClick={() => setLocale(loc)}
            >
              <Check
                className={`mr-2 h-4 w-4 ${loc === locale ? "opacity-100" : "opacity-0"}`}
              />
              {LOCALE_LABELS[loc]}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
