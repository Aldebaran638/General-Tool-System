import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { useI18n } from "@/i18n/I18nProvider"

import {
  listRecords,
  generateExport,
  listHistory,
  getExport,
  getSettings,
  updateSettings,
  purgeExpiredFiles,
  downloadExport,
} from "../api"
import type { RecordsQuery, GenerateRequest } from "../types"

export const reimbursementExportsQueryKey = ["reimbursement-exports"] as const
export const recordsQueryKey = (filters?: RecordsQuery) =>
  [...reimbursementExportsQueryKey, "records", filters ?? {}] as const
export const historyQueryKey = (filters?: object) =>
  [...reimbursementExportsQueryKey, "history", filters ?? {}] as const
export const settingsQueryKey = [...reimbursementExportsQueryKey, "settings"] as const
export const exportDetailQueryKey = (id: string) =>
  [...reimbursementExportsQueryKey, "detail", id] as const

export function useRecordsQuery(filters?: RecordsQuery) {
  return useQuery({
    queryKey: recordsQueryKey(filters),
    queryFn: () => listRecords(filters),
    retry: false,
  })
}

export function useHistoryQuery(filters?: {
  skip?: number
  limit?: number
  created_at_from?: string
  created_at_to?: string
  created_by_id?: string
  currency?: string
}) {
  return useQuery({
    queryKey: historyQueryKey(filters),
    queryFn: () => listHistory(filters),
    retry: false,
  })
}

export function useExportDetailQuery(exportId: string | null) {
  return useQuery({
    queryKey: exportDetailQueryKey(exportId ?? ""),
    queryFn: () => getExport(exportId as string),
    enabled: !!exportId,
    retry: false,
  })
}

export function useSettingsQuery() {
  return useQuery({
    queryKey: settingsQueryKey,
    queryFn: getSettings,
  })
}

export function useGenerateExportMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (data: GenerateRequest) => generateExport(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reimbursementExportsQueryKey })
      toast.success(t("finance.reimbursementExports.messages.generateSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.reimbursementExports.messages.generateFailed"),
      )
    },
  })
}

export function useUpdateSettingsMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (data: { retention_days?: number | null }) => updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsQueryKey })
      toast.success(t("finance.reimbursementExports.messages.settingsUpdateSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.reimbursementExports.messages.settingsUpdateFailed"),
      )
    },
  })
}

export function usePurgeExpiredFilesMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: purgeExpiredFiles,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: reimbursementExportsQueryKey })
      if (result.purged_count > 0) {
        toast.success(
          t("finance.reimbursementExports.messages.purgeSuccess").replace(
            "{count}",
            String(result.purged_count),
          ),
        )
      } else {
        toast.info(t("finance.reimbursementExports.messages.purgeEmpty"))
      }
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.reimbursementExports.messages.purgeFailed"),
      )
    },
  })
}

export { downloadExport }
