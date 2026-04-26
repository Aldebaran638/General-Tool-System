import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import type { InvoiceFileUpdate } from "../types"
import {
  listInvoiceFiles,
  createInvoiceFile,
  updateInvoiceFile,
  deleteInvoiceFile,
  confirmInvoiceFile,
  withdrawConfirmationInvoiceFile,
  voidInvoiceFile,
  restoreDraftInvoiceFile,
  restoreInvoiceFile,
  parsePreview,
} from "../api"
import { useI18n } from "@/i18n/I18nProvider"

export const invoiceFilesQueryKey = ["invoice-files"] as const

export function useInvoiceFilesQuery(deleted = false, status?: string) {
  return useQuery({
    queryKey: [...invoiceFilesQueryKey, { deleted, status }],
    queryFn: () => listInvoiceFiles({ deleted, status }),
  })
}

export function useParsePreviewMutation() {
  return useMutation({
    mutationFn: parsePreview,
  })
}

export function useCreateInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: createInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.createSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.saveFailed"))
    },
  })
}

export function useUpdateInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InvoiceFileUpdate }) =>
      updateInvoiceFile(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.updateSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.updateFailed"))
    },
  })
}

export function useConfirmInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: confirmInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.confirmSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.confirmFailed"))
    },
  })
}

export function useWithdrawConfirmationMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: withdrawConfirmationInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.withdrawSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.withdrawFailed"))
    },
  })
}

export function useVoidInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: voidInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.voidSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.voidFailed"))
    },
  })
}

export function useRestoreDraftMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: restoreDraftInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.restoreDraftSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.restoreDraftFailed"))
    },
  })
}

export function useDeleteInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: deleteInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.deleteSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.deleteFailed"))
    },
  })
}

export function useRestoreInvoiceFileMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: restoreInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success(t("finance.invoiceFiles.messages.restoreSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.invoiceFiles.messages.restoreFailed"))
    },
  })
}
