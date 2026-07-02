export function datetimeLocalToApi(value: string | null | undefined): string | undefined {
  if (!value) return undefined
  if (/(Z|[+-]\d{2}:\d{2})$/.test(value)) return value

  const valueWithSeconds = value.length === 16 ? `${value}:00` : value
  return new Date(valueWithSeconds).toISOString()
}

export function apiDatetimeToLocal(value: string): string {
  const date = new Date(value)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}
