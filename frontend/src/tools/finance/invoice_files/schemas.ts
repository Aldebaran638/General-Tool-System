import { z } from "zod"

export const CURRENCIES = [
  { value: "CNY", label: "CNY - 人民币" },
  { value: "USD", label: "USD - 美元" },
  { value: "EUR", label: "EUR - 欧元" },
  { value: "JPY", label: "JPY - 日元" },
  { value: "HKD", label: "HKD - 港币" },
  { value: "GBP", label: "GBP - 英镑" },
  { value: "AUD", label: "AUD - 澳元" },
  { value: "CAD", label: "CAD - 加元" },
  { value: "SGD", label: "SGD - 新加坡元" },
]

export const INVOICE_TYPES = [
  { value: "general_invoice", label: "普通发票" },
  { value: "vat_special_invoice", label: "增值税专用发票" },
  { value: "toll_invoice", label: "高速通行费" },
  { value: "other", label: "其他" },
]

export const invoiceFileFormSchema = z.object({
  invoice_number: z.string().min(1, { message: "发票号码是必填项" }),
  invoice_date: z.string().min(1, { message: "发票日期是必填项" }),
  invoice_amount: z.string().min(1, { message: "发票金额是必填项" }),
  tax_amount: z.string().optional(),
  currency: z.string().min(1, { message: "币种是必填项" }),
  buyer: z.string().min(1, { message: "购买方是必填项" }),
  seller: z.string().min(1, { message: "销售方是必填项" }),
  invoice_type: z.string().min(1, { message: "发票类型是必填项" }),
  note: z.string().optional(),
  pdf: z.instanceof(File).optional(),
})

export type InvoiceFileFormValues = z.infer<typeof invoiceFileFormSchema>
