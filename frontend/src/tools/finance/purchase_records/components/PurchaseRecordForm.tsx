import { zodResolver } from "@hookform/resolvers/zod"
import { Upload, X, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import type { PurchaseRecord } from "../types"
import {
  purchaseRecordFormSchema,
  type PurchaseRecordFormValues,
  CATEGORIES,
  SUBCATEGORIES,
  CURRENCIES,
} from "../schemas"
import {
  useCreatePurchaseRecordMutation,
  useUpdatePurchaseRecordMutation,
  useSubmitPurchaseRecordMutation,
  useOcrPreviewMutation,
} from "../hooks/usePurchaseRecords"

interface PurchaseRecordFormProps {
  open: boolean
  onClose: () => void
  record?: PurchaseRecord | null
}

export function PurchaseRecordForm({
  open,
  onClose,
  record,
}: PurchaseRecordFormProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [ocrError, setOcrError] = useState<string | null>(null)

  const createMutation = useCreatePurchaseRecordMutation()
  const updateMutation = useUpdatePurchaseRecordMutation()
  const submitMutation = useSubmitPurchaseRecordMutation()
  const ocrMutation = useOcrPreviewMutation()

  const isEditing = !!record

  const form = useForm<PurchaseRecordFormValues>({
    resolver: zodResolver(purchaseRecordFormSchema),
    defaultValues: {
      purchase_date: "",
      amount: "",
      currency: "",
      order_name: "",
      category: "",
      subcategory: null,
      note: "",
      screenshot: undefined,
    },
  })

  const watchCategory = form.watch("category")

  useEffect(() => {
    if (record) {
      form.reset({
        purchase_date: record.purchase_date,
        amount: record.amount,
        currency: record.currency,
        order_name: record.order_name,
        category: record.category,
        subcategory: record.subcategory,
        note: record.note || "",
        screenshot: undefined,
      })
    } else {
      form.reset({
        purchase_date: "",
        amount: "",
        currency: "",
        order_name: "",
        category: "",
        subcategory: null,
        note: "",
        screenshot: undefined,
      })
      setUploadedFile(null)
      setPreviewUrl(null)
      setOcrError(null)
    }
  }, [record, form, open])

  useEffect(() => {
    if (watchCategory !== "other_project") {
      form.setValue("subcategory", null)
    }
  }, [watchCategory, form])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadedFile(file)
    setOcrError(null)

    const url = URL.createObjectURL(file)
    setPreviewUrl(url)

    // Trigger OCR preview
    ocrMutation.mutate(file, {
      onSuccess: (data) => {
        if (data.purchase_date) {
          form.setValue("purchase_date", data.purchase_date)
        }
        if (data.amount) {
          form.setValue("amount", data.amount)
        }
        if (data.currency) {
          form.setValue("currency", data.currency)
        }
        if (data.order_name) {
          form.setValue("order_name", data.order_name)
        }
        if (data.category) {
          form.setValue("category", data.category)
        }
        if (data.subcategory) {
          form.setValue("subcategory", data.subcategory)
        }
        if (data.note) {
          form.setValue("note", data.note)
        }
      },
      onError: (error: Error) => {
        setOcrError(error.message || "OCR 识别失败，请手动填写")
      },
    })
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
    form.setValue("screenshot", undefined)
  }

  const onSubmit = (values: PurchaseRecordFormValues, submit = false) => {
    if (!isEditing && !uploadedFile) {
      form.setError("screenshot", {
        type: "manual",
        message: "请上传截图",
      })
      return
    }

    const data = {
      ...values,
      subcategory: values.subcategory || null,
    }

    if (isEditing && record) {
      const updateData: import("../types").PurchaseRecordUpdate = {
        purchase_date: data.purchase_date,
        amount: data.amount,
        currency: data.currency,
        order_name: data.order_name,
        category: data.category,
        subcategory: data.subcategory,
        note: data.note || null,
      }

      if (uploadedFile) {
        updateData.screenshot = uploadedFile
      }

      updateMutation.mutate(
        { id: record.id, data: updateData },
        {
          onSuccess: () => {
            if (submit) {
              submitMutation.mutate(record.id, {
                onSuccess: () => onClose(),
              })
            } else {
              onClose()
            }
          },
        },
      )
    } else {
      if (!uploadedFile) return

      createMutation.mutate(
        {
          ...data,
          screenshot: uploadedFile,
        } as import("../types").PurchaseRecordCreate,
        {
          onSuccess: (createdRecord) => {
            if (submit) {
              submitMutation.mutate(createdRecord.id, {
                onSuccess: () => onClose(),
              })
            } else {
              onClose()
            }
          },
        },
      )
    }
  }

  const handleSaveDraft = () => {
    form.handleSubmit((values) => onSubmit(values, false))()
  }

  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending ||
    ocrMutation.isPending

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "编辑购买记录" : "新建购买记录"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "修改购买记录信息"
              : "上传截图并填写购买记录信息"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4">
            {/* Screenshot Upload */}
            <FormField
              control={form.control}
              name="screenshot"
              render={() => (
                <FormItem>
                  <FormLabel>截图</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      {!previewUrl ? (
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                          <div className="flex flex-col items-center justify-center pt-5 pb-6">
                            <Upload className="w-8 h-8 mb-2 text-muted-foreground" />
                            <p className="text-sm text-muted-foreground">
                              点击上传截图
                            </p>
                          </div>
                          <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={handleFileChange}
                          />
                        </label>
                      ) : (
                        <div className="relative w-full h-32 rounded-lg overflow-hidden border">
                          <img
                            src={previewUrl}
                            alt="Screenshot preview"
                            className="w-full h-full object-contain bg-muted"
                          />
                          <button
                            type="button"
                            onClick={handleRemoveFile}
                            className="absolute top-2 right-2 p-1 bg-background/80 rounded-full hover:bg-background"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}

                      {ocrMutation.isPending && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          正在识别...
                        </div>
                      )}

                      {ocrError && (
                        <p className="text-sm text-destructive">{ocrError}</p>
                      )}

                      {form.formState.errors.screenshot && (
                        <p className="text-sm text-destructive">
                          {form.formState.errors.screenshot.message}
                        </p>
                      )}
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="purchase_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>购买日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>金额</FormLabel>
                    <FormControl>
                      <Input type="text" placeholder="0.00" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>币种</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择币种" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {CURRENCIES.map((currency) => (
                          <SelectItem
                            key={currency.value}
                            value={currency.value}
                          >
                            {currency.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="order_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>订单名称</FormLabel>
                    <FormControl>
                      <Input placeholder="输入订单名称" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>大类</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择大类" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {CATEGORIES.map((category) => (
                          <SelectItem
                            key={category.value}
                            value={category.value}
                          >
                            {category.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="subcategory"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>小类</FormLabel>
                    <Select
                      onValueChange={(value) =>
                        field.onChange(value || null)
                      }
                      value={field.value || ""}
                      disabled={watchCategory !== "other_project"}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择小类" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {SUBCATEGORIES.map((subcategory) => (
                          <SelectItem
                            key={subcategory.value}
                            value={subcategory.value}
                          >
                            {subcategory.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>备注</FormLabel>
                  <FormControl>
                    <Input placeholder="可选备注" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            variant="secondary"
            onClick={handleSaveDraft}
            disabled={isSubmitting}
          >
            {isSubmitting && createMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              "保存草稿"
            )}
          </Button>
          <Button
            onClick={() => form.handleSubmit((values) => onSubmit(values, true))()}
            disabled={isSubmitting}
          >
            {isSubmitting && submitMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                提交中...
              </>
            ) : (
              "保存并提交"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
