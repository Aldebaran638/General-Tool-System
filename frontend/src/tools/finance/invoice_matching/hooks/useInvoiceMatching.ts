import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { useI18n } from "@/i18n/I18nProvider"

import {
  approveMatch,
  cancelMatch,
  confirmMatch,
  getMatchSummary,
  listAllMatchesForAudit,
  listAvailableInvoices,
  listCandidates,
  listMatches,
  listUnmatchedPurchaseRecords,
  reconfirmMatch,
  searchAvailableInvoices,
  unapproveMatch,
} from "../api"
import type { ConfirmMatchRequest, MatchStatus } from "../types"

export const invoiceMatchingQueryKey = ["invoice-matching"] as const
export const invoiceMatchingSummaryKey = [
  ...invoiceMatchingQueryKey,
  "summary",
] as const
export const invoiceMatchingUnmatchedKey = [
  ...invoiceMatchingQueryKey,
  "unmatched",
] as const
export const invoiceMatchingAvailableInvoicesKey = [
  ...invoiceMatchingQueryKey,
  "available-invoices",
] as const
export const invoiceMatchingMatchesKey = (status?: MatchStatus) =>
  [...invoiceMatchingQueryKey, "matches", status ?? "all"] as const
export const invoiceMatchingAuditKey = (status?: MatchStatus) =>
  [...invoiceMatchingQueryKey, "audit", status ?? "all"] as const
export const invoiceMatchingCandidatesKey = (purchaseRecordId: string) =>
  [...invoiceMatchingQueryKey, "candidates", purchaseRecordId] as const
export const invoiceMatchingSearchKey = (
  purchaseRecordId: string,
  search: string,
) =>
  [
    ...invoiceMatchingQueryKey,
    "search-invoices",
    purchaseRecordId,
    search,
  ] as const

export function useMatchSummaryQuery() {
  return useQuery({
    queryKey: invoiceMatchingSummaryKey,
    queryFn: getMatchSummary,
  })
}

export function useUnmatchedPurchaseRecordsQuery() {
  return useQuery({
    queryKey: invoiceMatchingUnmatchedKey,
    queryFn: () => listUnmatchedPurchaseRecords(),
  })
}

export function useAvailableInvoicesQuery() {
  return useQuery({
    queryKey: invoiceMatchingAvailableInvoicesKey,
    queryFn: () => listAvailableInvoices(),
  })
}

export function useCandidatesQuery(
  purchaseRecordId: string | null,
  enabled: boolean = true,
) {
  return useQuery({
    queryKey: invoiceMatchingCandidatesKey(purchaseRecordId ?? ""),
    queryFn: () => listCandidates(purchaseRecordId as string),
    enabled: enabled && !!purchaseRecordId,
    retry: false,
  })
}

export function useMatchesQuery(status?: MatchStatus) {
  return useQuery({
    queryKey: invoiceMatchingMatchesKey(status),
    queryFn: () => listMatches(status ? { status } : undefined),
  })
}

export function useAllMatchesForAuditQuery(status?: MatchStatus) {
  return useQuery({
    queryKey: invoiceMatchingAuditKey(status),
    queryFn: () => listAllMatchesForAudit(status ? { status } : undefined),
  })
}

export function useSearchAvailableInvoicesQuery(
  purchaseRecordId: string | null,
  search: string,
  enabled: boolean = true,
) {
  return useQuery({
    queryKey: invoiceMatchingSearchKey(purchaseRecordId ?? "", search),
    queryFn: () =>
      searchAvailableInvoices({
        purchase_record_id: purchaseRecordId as string,
        search,
      }),
    enabled: enabled && !!purchaseRecordId && search.trim().length > 0,
    retry: false,
  })
}

function invalidateAll(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: invoiceMatchingQueryKey })
}

export function useConfirmMatchMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (data: ConfirmMatchRequest) => confirmMatch(data),
    onSuccess: () => {
      invalidateAll(queryClient)
      toast.success(t("finance.invoiceMatching.messages.confirmSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.invoiceMatching.messages.confirmFailed"),
      )
    },
  })
}

export function useCancelMatchMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (matchId: string) => cancelMatch(matchId),
    onSuccess: () => {
      invalidateAll(queryClient)
      toast.success(t("finance.invoiceMatching.messages.cancelSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.invoiceMatching.messages.cancelFailed"),
      )
    },
  })
}

export function useReconfirmMatchMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (matchId: string) => reconfirmMatch(matchId),
    onSuccess: () => {
      invalidateAll(queryClient)
      toast.success(t("finance.invoiceMatching.messages.reconfirmSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.invoiceMatching.messages.reconfirmFailed"),
      )
    },
  })
}

export function useApproveMatchMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (matchId: string) => approveMatch(matchId),
    onSuccess: () => {
      invalidateAll(queryClient)
      toast.success(t("finance.invoiceMatching.messages.approveSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.invoiceMatching.messages.approveFailed"),
      )
    },
  })
}

export function useUnapproveMatchMutation() {
  const queryClient = useQueryClient()
  const { t } = useI18n()

  return useMutation({
    mutationFn: (matchId: string) => unapproveMatch(matchId),
    onSuccess: () => {
      invalidateAll(queryClient)
      toast.success(t("finance.invoiceMatching.messages.unapproveSuccess"))
    },
    onError: (error: Error) => {
      toast.error(
        error.message || t("finance.invoiceMatching.messages.unapproveFailed"),
      )
    },
  })
}
