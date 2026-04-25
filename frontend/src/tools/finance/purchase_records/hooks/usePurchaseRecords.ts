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

  return useMutation({
    mutationFn: createPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已保存为草稿")
    },
    onError: (error: Error) => {
      toast.error(error.message || "保存失败")
    },
  })
}

export function useUpdatePurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PurchaseRecordUpdate }) =>
      updatePurchaseRecord(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已更新")
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新失败")
    },
  })
}

export function useSubmitPurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: submitPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已提交")
    },
    onError: (error: Error) => {
      toast.error(error.message || "提交失败")
    },
  })
}

export function useWithdrawPurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: withdrawPurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("提交已撤回")
    },
    onError: (error: Error) => {
      toast.error(error.message || "撤回失败")
    },
  })
}

export function useApprovePurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: approvePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已批准")
    },
    onError: (error: Error) => {
      toast.error(error.message || "批准失败")
    },
  })
}

export function useRejectPurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RejectRequest }) =>
      rejectPurchaseRecord(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已驳回")
    },
    onError: (error: Error) => {
      toast.error(error.message || "驳回失败")
    },
  })
}

export function useUnapprovePurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: unapprovePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("批准已撤回")
    },
    onError: (error: Error) => {
      toast.error(error.message || "撤回批准失败")
    },
  })
}

export function useDeletePurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deletePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已删除")
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除失败")
    },
  })
}

export function useRestorePurchaseRecordMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: restorePurchaseRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchaseRecordsQueryKey })
      toast.success("购买记录已恢复")
    },
    onError: (error: Error) => {
      toast.error(error.message || "恢复失败")
    },
  })
}
