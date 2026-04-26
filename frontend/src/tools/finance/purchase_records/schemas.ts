import { z } from "zod"

export interface PurchaseRecordFormValues {
  purchase_date: string
  amount: string
  currency: string
  order_name: string
  category: string
  subcategory?: string | null
  note?: string
  screenshot?: File
}

export interface RejectFormValues {
  reason: string
}

export function createPurchaseRecordSchemas(t: (key: string) => string) {
  const CURRENCIES = [
    { value: "CNY", label: `CNY - ${t("finance.purchaseRecords.currency.CNY")}` },
    { value: "USD", label: `USD - ${t("finance.purchaseRecords.currency.USD")}` },
    { value: "EUR", label: `EUR - ${t("finance.purchaseRecords.currency.EUR")}` },
    { value: "JPY", label: `JPY - ${t("finance.purchaseRecords.currency.JPY")}` },
    { value: "HKD", label: `HKD - ${t("finance.purchaseRecords.currency.HKD")}` },
    { value: "GBP", label: `GBP - ${t("finance.purchaseRecords.currency.GBP")}` },
    { value: "AUD", label: `AUD - ${t("finance.purchaseRecords.currency.AUD")}` },
    { value: "CAD", label: `CAD - ${t("finance.purchaseRecords.currency.CAD")}` },
    { value: "SGD", label: `SGD - ${t("finance.purchaseRecords.currency.SGD")}` },
  ]

  const CATEGORIES = [
    { value: "transportation", label: t("finance.purchaseRecords.category.transportation") },
    { value: "meals_entertainment", label: t("finance.purchaseRecords.category.meals_entertainment") },
    { value: "vehicle", label: t("finance.purchaseRecords.category.vehicle") },
    { value: "other_project", label: t("finance.purchaseRecords.category.other_project") },
  ]

  const SUBCATEGORIES = [
    { value: "agv", label: t("finance.purchaseRecords.subcategory.agv") },
    { value: "painting_robot", label: t("finance.purchaseRecords.subcategory.painting_robot") },
    { value: "rebar_robot", label: t("finance.purchaseRecords.subcategory.rebar_robot") },
    { value: "fleet_scheduling", label: t("finance.purchaseRecords.subcategory.fleet_scheduling") },
    { value: "rd_expense", label: t("finance.purchaseRecords.subcategory.rd_expense") },
  ]

  const purchaseRecordFormSchema = z
    .object({
      purchase_date: z.string().min(1, { message: t("finance.purchaseRecords.validation.purchaseDateRequired") }),
      amount: z.string().min(1, { message: t("finance.purchaseRecords.validation.amountRequired") }),
      currency: z.string().min(1, { message: t("finance.purchaseRecords.validation.currencyRequired") }),
      order_name: z.string().min(1, { message: t("finance.purchaseRecords.validation.orderNameRequired") }),
      category: z.string().min(1, { message: t("finance.purchaseRecords.validation.categoryRequired") }),
      subcategory: z.string().nullable().optional(),
      note: z.string().optional(),
      screenshot: z.instanceof(File).optional(),
    })
    .refine(
      (data) => {
        if (data.category !== "other_project") {
          return !data.subcategory || data.subcategory === null
        }
        return true
      },
      {
        message: t("finance.purchaseRecords.validation.subcategoryEmpty"),
        path: ["subcategory"],
      },
    )

  const rejectFormSchema = z.object({
    reason: z.string().min(1, { message: t("finance.purchaseRecords.validation.rejectReasonRequired") }),
  })

  return { CURRENCIES, CATEGORIES, SUBCATEGORIES, purchaseRecordFormSchema, rejectFormSchema }
}
