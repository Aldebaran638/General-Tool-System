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

export const equipmentPurchaseFillerQueryKey = ["equipment-purchase-filler"] as const

export function useEquipmentPurchaseFieldsQuery() {
  return useQuery({
    queryKey: [...equipmentPurchaseFillerQueryKey, "fields"],
    queryFn: listFields,
  })
}

export function useEquipmentPurchasePreviewQuery() {
  return useQuery({
    queryKey: [...equipmentPurchaseFillerQueryKey, "preview"],
    queryFn: getPreview,
  })
}

export function useEquipmentPurchaseVersionsQuery() {
  return useQuery({
    queryKey: [...equipmentPurchaseFillerQueryKey, "versions"],
    queryFn: listVersions,
  })
}

export function useEquipmentPurchaseVersionQuery(id: string | null) {
  return useQuery({
    queryKey: [...equipmentPurchaseFillerQueryKey, "versions", id],
    queryFn: () => getVersion(id!),
    enabled: !!id,
  })
}

export function useCreateEquipmentPurchaseVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: createVersion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equipmentPurchaseFillerQueryKey })
      toast.success(t("contracts.equipmentPurchase.toast.versionSaved"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.equipmentPurchase.toast.saveFailed"))
    },
  })
}

export function useUpdateEquipmentPurchaseVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FilledVersionUpdate }) =>
      updateVersion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equipmentPurchaseFillerQueryKey })
      toast.success(t("contracts.equipmentPurchase.toast.versionUpdated"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.equipmentPurchase.toast.updateFailed"))
    },
  })
}

export function useDeleteEquipmentPurchaseVersionMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: deleteVersion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equipmentPurchaseFillerQueryKey })
      toast.success(t("contracts.equipmentPurchase.toast.versionDeleted"))
    },
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.equipmentPurchase.toast.deleteFailed"))
    },
  })
}

export function useExportEquipmentPurchaseVersionMutation() {
  const { t } = useI18n()

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request?: ExportRequest }) =>
      exportVersion(id, request),
    onError: (error: Error) => {
      toast.error(error.message || t("contracts.equipmentPurchase.toast.exportFailed"))
    },
  })
}
