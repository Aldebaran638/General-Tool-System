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

  return useMutation({
    mutationFn: createInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票文件已保存为草稿")
    },
    onError: (error: Error) => {
      toast.error(error.message || "保存失败")
    },
  })
}

export function useUpdateInvoiceFileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InvoiceFileUpdate }) =>
      updateInvoiceFile(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票文件已更新")
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新失败")
    },
  })
}

export function useConfirmInvoiceFileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: confirmInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票已确认")
    },
    onError: (error: Error) => {
      toast.error(error.message || "确认失败")
    },
  })
}

export function useWithdrawConfirmationMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: withdrawConfirmationInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("确认已撤回")
    },
    onError: (error: Error) => {
      toast.error(error.message || "撤回确认失败")
    },
  })
}

export function useVoidInvoiceFileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: voidInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票已作废")
    },
    onError: (error: Error) => {
      toast.error(error.message || "作废失败")
    },
  })
}

export function useRestoreDraftMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: restoreDraftInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票已恢复为草稿")
    },
    onError: (error: Error) => {
      toast.error(error.message || "恢复草稿失败")
    },
  })
}

export function useDeleteInvoiceFileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票文件已删除")
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除失败")
    },
  })
}

export function useRestoreInvoiceFileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: restoreInvoiceFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceFilesQueryKey })
      toast.success("发票文件已恢复")
    },
    onError: (error: Error) => {
      toast.error(error.message || "恢复失败")
    },
  })
}
