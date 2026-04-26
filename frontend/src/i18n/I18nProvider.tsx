import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react"
import {
  type Locale,
  DEFAULT_LOCALE,
  detectBrowserLocale,
  getStoredLocale,
  storeLocale,
} from "./locales"
import type { DeepStringRecord } from "./types"
import zhCN from "./dictionaries/zh-CN/index"
import enUS from "./dictionaries/en-US/index"
import zhTW from "./dictionaries/zh-TW/index"

const dictionaries: Record<Locale, DeepStringRecord> = {
  "zh-CN": zhCN,
  "en-US": enUS,
  "zh-TW": zhTW,
}

function getInitialLocale(): Locale {
  const stored = getStoredLocale()
  if (stored) return stored
  const detected = detectBrowserLocale() ?? DEFAULT_LOCALE
  // Persist resolved default so reload sees the same locale and external observers (e.g. tests) read a consistent value.
  storeLocale(detected)
  return detected
}

function getNestedValue(obj: DeepStringRecord, path: string): string | undefined {
  const parts = path.split(".")
  let current: DeepStringRecord | string | undefined = obj
  for (const part of parts) {
    if (typeof current !== "object" || current === null) return undefined
    current = current[part]
  }
  return typeof current === "string" ? current : undefined
}

export interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextValue>({
  locale: DEFAULT_LOCALE,
  setLocale: () => {},
  t: (key: string) => key,
})

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale)

  const setLocale = useCallback((next: Locale) => {
    storeLocale(next)
    setLocaleState(next)
  }, [])

  const t = useCallback(
    (key: string) => {
      const dict = (dictionaries as Record<string, DeepStringRecord>)[locale]
      const value = getNestedValue(dict, key)
      if (value === undefined) {
        return key
      }
      return value
    },
    [locale],
  )

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext)
}
