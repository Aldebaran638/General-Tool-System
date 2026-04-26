export const EXPORTED_FILTER_OPTIONS = [
  { value: "all", labelKey: "finance.reimbursementExports.filters.exportedAll" },
  { value: "exported", labelKey: "finance.reimbursementExports.filters.exportedExported" },
  { value: "not_exported", labelKey: "finance.reimbursementExports.filters.exportedNotExported" },
] as const

export const CATEGORY_OPTIONS = [
  { value: "transportation", labelKey: "finance.purchaseRecords.category.transportation" },
  { value: "meals_entertainment", labelKey: "finance.purchaseRecords.category.meals_entertainment" },
  { value: "vehicle", labelKey: "finance.purchaseRecords.category.vehicle" },
  { value: "other_project", labelKey: "finance.purchaseRecords.category.other_project" },
] as const
