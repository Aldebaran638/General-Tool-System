const LOGIN_RETURN_TO_KEY = "login_return_to"

function safeInternalPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/"
  return value
}

export function rememberLoginReturnTo(path: string): void {
  sessionStorage.setItem(LOGIN_RETURN_TO_KEY, safeInternalPath(path))
}

export function consumeLoginReturnTo(): string {
  const path = safeInternalPath(sessionStorage.getItem(LOGIN_RETURN_TO_KEY))
  sessionStorage.removeItem(LOGIN_RETURN_TO_KEY)
  return path
}
