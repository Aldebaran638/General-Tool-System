import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import type { PurchaseRecordUpdate, RejectRequest } from "../types"
import {
  listPurchaseRecords,
  createPurchaseRecord,
  updatePurchaseRecord,
  deletePurchaseRecord,
  submitPurchaseRecord,
  withdrawPurchaseRecord,
  approvePurchaseRecord,
  rejectPurchaseRecord,
  unapprovePurchaseRecord,
  restorePurchaseRecord,
  ocrPreview,
} from "../api"
import { useI18n } from "@/i18n/I18nProvider"

export const purchaseRecordsQueryKey = ["purchase-records"] as const

export function usePurchaseRecordsQuery(deleted = false) {
  return useQuery({
    queryKey: [...purchaseRecordsQueryKey, { deleted }],
    queryFn: () => listPurchaseRecords({ deleted }),
  })
}

export function useOcrPreviewMutation() {
  return useMutation({
    mutationFn: ocrPreview,
  })
}

export function useCreatePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: createPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.createSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.saveFailed"))
    },
  })
}

export function useUpdatePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PurchaseRecordUpdate }) =>
      updatePurchaseRecord(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.updateSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.updateFailed"))
    },
  })
}

export function useSubmitPurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: submitPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.submitSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.submitFailed"))
    },
  })
}

export function useWithdrawPurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: withdrawPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.withdrawSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.withdrawFailed"))
    },
  })
}

export function useApprovePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: approvePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.approveSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.approveFailed"))
    },
  })
}

export function useRejectPurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RejectRequest }) =>
      rejectPurchaseRecord(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.rejectSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.rejectFailed"))
    },
  })
}

export function useUnapprovePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: unapprovePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.unapproveSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.unapproveFailed"))
    },
  })
}

export function useDeletePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: deletePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.deleteSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.deleteFailed"))
    },
  })
}

export function useRestorePurchaseRecordMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: restorePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success(t("finance.purchaseRecords.messages.restoreSuccess"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("finance.purchaseRecords.messages.restoreFailed"))
    },
  })
}
