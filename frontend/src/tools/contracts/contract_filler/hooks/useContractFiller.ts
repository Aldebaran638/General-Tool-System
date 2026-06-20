import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { useI18n } from "@/i18n/I18nProvider"

import {
  createVersion,
  deleteVersion,
  exportVersion,
  getPreview,
  getVersion,
  listFields,
  listVersions,
  updateVersion,
} from "../api"
import type { ExportRequest, FilledVersionUpdate } from "../types"

export const contractFillerQueryKey = ["contract-filler"] as const

export function useContractFieldsQuery() {
  return useQuery({
    queryKey: [...contractFillerQueryKey, "fields"],
    queryFn: listFields,
  })
}

export function useContractPreviewQuery() {
  return useQuery({
    queryKey: [...contractFillerQueryKey, "preview"],
    queryFn: getPreview,
  })
}

export function useContractVersionsQuery() {
  return useQuery({
    queryKey: [...contractFillerQueryKey, "versions"],
    queryFn: listVersions,
  })
}

export function useContractVersionQuery(id: string | null) {
  return useQuery({
    queryKey: [...contractFillerQueryKey, "versions", id],
    queryFn: () => getVersion(id!),
    enabled: !!id,
  })
}

export function useCreateVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: createVersion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractFillerQueryKey })
      toast.success(t("contracts.contractFiller.toast.versionSaved"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.contractFiller.toast.saveFailed"))
    },
  })
}

export function useUpdateVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FilledVersionUpdate }) =>
      updateVersion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractFillerQueryKey })
      toast.success(t("contracts.contractFiller.toast.versionUpdated"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.contractFiller.toast.updateFailed"))
    },
  })
}

export function useDeleteVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: deleteVersion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractFillerQueryKey })
      toast.success(t("contracts.contractFiller.toast.versionDeleted"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.contractFiller.toast.deleteFailed"))
    },
  })
}

export function useExportVersionMutation() {
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request?: ExportRequest }) =>
      exportVersion(id, request),
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.contractFiller.toast.exportFailed"))
    },
  })
}
