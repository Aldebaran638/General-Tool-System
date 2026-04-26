export type Locale = "zh-CN" | "en-US" | "zh-TW"

export const DEFAULT_LOCALE: Locale = "zh-CN"
export const STORAGE_KEY = "app_locale"
export const SUPPORTED_LOCALES: Locale[] = ["zh-CN", "en-US", "zh-TW"]

export const LOCALE_LABELS: Record<Locale, string> = {
  "zh-CN": "简体中文",
  "en-US": "English",
  "zh-TW": "繁體中文",
}

export function detectBrowserLocale(): Locale {
  const lang = navigator.language || (navigator as any).userLanguage || "zh-CN"
  if (lang.startsWith("zh")) {
    return lang.includes("TW") || lang.includes("HK") ? "zh-TW" : "zh-CN"
  }
  if (lang.startsWith("en")) return "en-US"
  return DEFAULT_LOCALE
}

export function getStoredLocale(): Locale | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && SUPPORTED_LOCALES.includes(stored as Locale)) {
      return stored as Locale
    }
  } catch {
    // localStorage may not be available
  }
  return null
}

export function storeLocale(locale: Locale): void {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // localStorage may not be available
  }
}
