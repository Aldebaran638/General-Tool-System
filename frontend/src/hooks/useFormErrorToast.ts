import { useEffect, useRef } from "react"
import type { FieldErrors, FieldValues } from "react-hook-form"
import { toast } from "sonner"

const TOAST_ID_PREFIX = "form-error"

function extractMessage(error: unknown): string | null {
  if (!error || typeof error !== "object") return null
  const message = (error as { message?: unknown }).message
  return typeof message === "string" && message.length > 0 ? message : null
}

/**
 * Surfaces react-hook-form validation errors as closable toast notifications
 * instead of inline messages, so error states never shift the page layout.
 *
 * Toasts fire when a new (field, message) pair appears (on blur or submit),
 * are deduped per field via a stable toast id, and a field's entry resets
 * once its error resolves so a re-occurring error toasts again.
 */
export function useFormErrorToast<TFieldValues extends FieldValues>(
  errors: FieldErrors<TFieldValues>,
) {
  const shownRef = useRef<Map<string, string>>(new Map())

  useEffect(() => {
    const shown = shownRef.current
    const activeFields = new Set<string>()

    for (const [field, error] of Object.entries(errors)) {
      const message = extractMessage(error)
      if (!message) continue
      activeFields.add(field)
      if (shown.get(field) !== message) {
        shown.set(field, message)
        toast.error(message, { id: `${TOAST_ID_PREFIX}-${field}` })
      }
    }

    for (const field of [...shown.keys()]) {
      if (!activeFields.has(field)) {
        shown.delete(field)
      }
    }
  }, [errors])
}

/**
 * Re-affirm the first validation error on submit, even if it was already
 * toasted on blur. The per-field toast id prevents duplicates from stacking.
 */
export function toastFirstFormError<TFieldValues extends FieldValues>(
  errors: FieldErrors<TFieldValues>,
) {
  const [field, error] = Object.entries(errors)[0] ?? []
  const message = extractMessage(error)
  if (field && message) {
    toast.error(message, { id: `${TOAST_ID_PREFIX}-${field}` })
  }
}
