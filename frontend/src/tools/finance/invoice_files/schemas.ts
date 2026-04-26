import { z } from "zod"

export interface InvoiceFileFormValues {
  invoice_number: string
  invoice_date: string
  invoice_amount: string
  tax_amount?: string
  currency: string
  buyer: string
  seller: string
  invoice_type: string
  note?: string
  pdf?: File
}

export function createInvoiceFileSchemas(t: (key: string) => string) {
  const CURRENCIES = [
    { value: "CNY", label: `CNY - ${t("finance.invoiceFiles.currency.CNY")}` },
    { value: "USD", label: `USD - ${t("finance.invoiceFiles.currency.USD")}` },
    { value: "EUR", label: `EUR - ${t("finance.invoiceFiles.currency.EUR")}` },
    { value: "JPY", label: `JPY - ${t("finance.invoiceFiles.currency.JPY")}` },
    { value: "HKD", label: `HKD - ${t("finance.invoiceFiles.currency.HKD")}` },
    { value: "GBP", label: `GBP - ${t("finance.invoiceFiles.currency.GBP")}` },
    { value: "AUD", label: `AUD - ${t("finance.invoiceFiles.currency.AUD")}` },
    { value: "CAD", label: `CAD - ${t("finance.invoiceFiles.currency.CAD")}` },
    { value: "SGD", label: `SGD - ${t("finance.invoiceFiles.currency.SGD")}` },
  ]

  const INVOICE_TYPES = [
    { value: "general_invoice", label: t("finance.invoiceFiles.invoiceType.general_invoice") },
    { value: "vat_special_invoice", label: t("finance.invoiceFiles.invoiceType.vat_special_invoice") },
    { value: "toll_invoice", label: t("finance.invoiceFiles.invoiceType.toll_invoice") },
    { value: "other", label: t("finance.invoiceFiles.invoiceType.other") },
  ]

  const invoiceFileFormSchema = z.object({
    invoice_number: z.string().min(1, { message: t("finance.invoiceFiles.validation.invoiceNumberRequired") }),
    invoice_date: z.string().min(1, { message: t("finance.invoiceFiles.validation.invoiceDateRequired") }),
    invoice_amount: z.string().min(1, { message: t("finance.invoiceFiles.validation.invoiceAmountRequired") }),
    tax_amount: z.string().optional(),
    currency: z.string().min(1, { message: t("finance.invoiceFiles.validation.currencyRequired") }),
    buyer: z.string().min(1, { message: t("finance.invoiceFiles.validation.buyerRequired") }),
    seller: z.string().min(1, { message: t("finance.invoiceFiles.validation.sellerRequired") }),
    invoice_type: z.string().min(1, { message: t("finance.invoiceFiles.validation.invoiceTypeRequired") }),
    note: z.string().optional(),
    pdf: z.instanceof(File).optional(),
  })

  return { CURRENCIES, INVOICE_TYPES, invoiceFileFormSchema }
}
