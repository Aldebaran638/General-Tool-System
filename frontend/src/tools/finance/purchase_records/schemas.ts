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

export const CATEGORIES = [
  { value: "transportation", label: "交通费用" },
  { value: "meals_entertainment", label: "膳食 / 应酬费用" },
  { value: "vehicle", label: "汽车费用" },
  { value: "other_project", label: "其他项目费用" },
]

export const SUBCATEGORIES = [
  { value: "agv", label: "自动导航承载车" },
  { value: "painting_robot", label: "智能喷漆机器人" },
  { value: "rebar_robot", label: "钢筋折弯与结扎机器人" },
  { value: "fleet_scheduling", label: "生产线车队调度" },
  { value: "rd_expense", label: "研发部开销" },
]

export const purchaseRecordFormSchema = z
  .object({
    purchase_date: z.string().min(1, { message: "购买日期是必填项" }),
    amount: z.string().min(1, { message: "金额是必填项" }),
    currency: z.string().min(1, { message: "币种是必填项" }),
    order_name: z.string().min(1, { message: "订单名称是必填项" }),
    category: z.string().min(1, { message: "大类是必填项" }),
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
      message: "非「其他项目费用」时小类必须为空",
      path: ["subcategory"],
    },
  )

export type PurchaseRecordFormValues = z.infer<typeof purchaseRecordFormSchema>

export const rejectFormSchema = z.object({
  reason: z.string().min(1, { message: "驳回原因是必填项" }),
})

export type RejectFormValues = z.infer<typeof rejectFormSchema>
