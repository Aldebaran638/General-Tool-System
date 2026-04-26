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
  createPurchaseRecordSchemas,
  type PurchaseRecordFormValues,
} from "../schemas"
import {
  useCreatePurchaseRecordMutation,
  useUpdatePurchaseRecordMutation,
  useSubmitPurchaseRecordMutation,
  useOcrPreviewMutation,
} from "../hooks/usePurchaseRecords"
import { useI18n } from "@/i18n/I18nProvider"

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
  const { t } = useI18n()
  const { purchaseRecordFormSchema, CURRENCIES, CATEGORIES, SUBCATEGORIES } = createPurchaseRecordSchemas(t)

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
        setOcrError(error.message || t("finance.purchaseRecords.messages.ocrFailed"))
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
        message: t("finance.purchaseRecords.validation.screenshotRequired"),
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
            {isEditing ? t("finance.purchaseRecords.form.titleEdit") : t("finance.purchaseRecords.form.titleCreate")}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? t("finance.purchaseRecords.form.descriptionEdit")
              : t("finance.purchaseRecords.form.descriptionCreate")}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4">
            <FormField
              control={form.control}
              name="screenshot"
              render={() => (
                <FormItem>
                  <FormLabel>{t("finance.purchaseRecords.form.screenshot")}</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      {!previewUrl ? (
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                          <div className="flex flex-col items-center justify-center pt-5 pb-6">
                            <Upload className="w-8 h-8 mb-2 text-muted-foreground" />
                            <p className="text-sm text-muted-foreground">
                              {t("finance.purchaseRecords.form.clickToUpload")}
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
                          {t("common.loading")}
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
                    <FormLabel>{t("finance.purchaseRecords.form.purchaseDate")}</FormLabel>
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
                    <FormLabel>{t("finance.purchaseRecords.form.amount")}</FormLabel>
                    <FormControl>
                      <Input type="text" placeholder={t("finance.purchaseRecords.form.amountPlaceholder")} {...field} />
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
                    <FormLabel>{t("finance.purchaseRecords.form.currency")}</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={t("finance.purchaseRecords.form.currencyPlaceholder")} />
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
                    <FormLabel>{t("finance.purchaseRecords.form.orderName")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.purchaseRecords.form.orderNamePlaceholder")} {...field} />
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
                    <FormLabel>{t("finance.purchaseRecords.form.category")}</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={t("finance.purchaseRecords.form.categoryPlaceholder")} />
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
                    <FormLabel>{t("finance.purchaseRecords.form.subcategory")}</FormLabel>
                    <Select
                      onValueChange={(value) =>
                        field.onChange(value || null)
                      }
                      value={field.value || ""}
                      disabled={watchCategory !== "other_project"}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={t("finance.purchaseRecords.form.subcategoryPlaceholder")} />
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
                  <FormLabel>{t("finance.purchaseRecords.form.note")}</FormLabel>
                  <FormControl>
                    <Input placeholder={t("finance.purchaseRecords.form.notePlaceholder")} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            {t("finance.purchaseRecords.form.cancel")}
          </Button>
          <Button
            variant="secondary"
            onClick={handleSaveDraft}
            disabled={isSubmitting}
          >
            {isSubmitting && createMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("finance.purchaseRecords.form.saving")}
              </>
            ) : (
              t("finance.purchaseRecords.form.saveDraft")
            )}
          </Button>
          <Button
            onClick={() => form.handleSubmit((values) => onSubmit(values, true))()}
            disabled={isSubmitting}
          >
            {isSubmitting && submitMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("finance.purchaseRecords.form.submitting")}
              </>
            ) : (
              t("finance.purchaseRecords.form.saveAndSubmit")
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
