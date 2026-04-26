import { zodResolver } from "@hookform/resolvers/zod"
import { Upload, X, Loader2, FileText } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"

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

import type { InvoiceFile } from "../types"
import {
  createInvoiceFileSchemas,
  type InvoiceFileFormValues,
} from "../schemas"
import {
  useCreateInvoiceFileMutation,
  useUpdateInvoiceFileMutation,
  useParsePreviewMutation,
} from "../hooks/useInvoiceFiles"
import { useI18n } from "@/i18n/I18nProvider"

interface InvoiceFileFormProps {
  open: boolean
  onClose: () => void
  record?: InvoiceFile | null
}

export function InvoiceFileForm({
  open,
  onClose,
  record,
}: InvoiceFileFormProps) {
  const { t } = useI18n()
  const { invoiceFileFormSchema, CURRENCIES, INVOICE_TYPES } = createInvoiceFileSchemas(t)

  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)

  const createMutation = useCreateInvoiceFileMutation()
  const updateMutation = useUpdateInvoiceFileMutation()
  const parseMutation = useParsePreviewMutation()

  const isEditing = !!record

  const form = useForm<InvoiceFileFormValues>({
    resolver: zodResolver(invoiceFileFormSchema),
    defaultValues: {
      invoice_number: "",
      invoice_date: "",
      invoice_amount: "",
      tax_amount: "",
      currency: "",
      buyer: "",
      seller: "",
      invoice_type: "",
      note: "",
      pdf: undefined,
    },
  })

  useEffect(() => {
    if (record) {
      form.reset({
        invoice_number: record.invoice_number,
        invoice_date: record.invoice_date,
        invoice_amount: record.invoice_amount,
        tax_amount: record.tax_amount || "",
        currency: record.currency,
        buyer: record.buyer,
        seller: record.seller,
        invoice_type: record.invoice_type,
        note: record.note || "",
        pdf: undefined,
      })
    } else {
      form.reset({
        invoice_number: "",
        invoice_date: "",
        invoice_amount: "",
        tax_amount: "",
        currency: "",
        buyer: "",
        seller: "",
        invoice_type: "",
        note: "",
        pdf: undefined,
      })
      setUploadedFile(null)
      setPreviewUrl(null)
      setParseError(null)
    }
  }, [record, form, open])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setParseError(null)

    parseMutation.mutate(file, {
      onSuccess: (data) => {
        if (data.invoice_number) {
          form.setValue("invoice_number", data.invoice_number)
        }
        if (data.invoice_date) {
          form.setValue("invoice_date", data.invoice_date)
        }
        if (data.invoice_amount) {
          form.setValue("invoice_amount", data.invoice_amount)
        }
        if (data.tax_amount) {
          form.setValue("tax_amount", data.tax_amount)
        }
        if (data.currency) {
          form.setValue("currency", data.currency)
        }
        if (data.buyer) {
          form.setValue("buyer", data.buyer)
        }
        if (data.seller) {
          form.setValue("seller", data.seller)
        }
        if (data.invoice_type) {
          form.setValue("invoice_type", data.invoice_type)
        }
      },
      onError: () => {
        setParseError(t("finance.invoiceFiles.form.parseFailed"))
      },
    })
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    setParseError(null)
  }

  const onSubmit = (values: InvoiceFileFormValues) => {
    if (!isEditing && !uploadedFile) {
      toast.error(t("finance.invoiceFiles.validation.pdfRequired"))
      return
    }

    if (isEditing && record) {
      updateMutation.mutate(
        {
          id: record.id,
          data: {
            ...values,
            pdf: uploadedFile || undefined,
          },
        },
        {
          onSuccess: () => {
            onClose()
          },
        },
      )
    } else {
      if (!uploadedFile) return
      createMutation.mutate(
        {
          invoice_number: values.invoice_number,
          invoice_date: values.invoice_date,
          invoice_amount: values.invoice_amount,
          tax_amount: values.tax_amount || "0.00",
          currency: values.currency,
          buyer: values.buyer,
          seller: values.seller,
          invoice_type: values.invoice_type,
          note: values.note,
          pdf: uploadedFile,
        },
        {
          onSuccess: () => {
            onClose()
          },
        },
      )
    }
  }

  const handleSaveDraft = () => {
    form.handleSubmit((values) => onSubmit(values))()
  }

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? t("finance.invoiceFiles.form.titleEdit") : t("finance.invoiceFiles.form.titleCreate")}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? t("finance.invoiceFiles.form.descriptionEdit")
              : t("finance.invoiceFiles.form.descriptionCreate")}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4">
            <FormField
              control={form.control}
              name="pdf"
              render={() => (
                <FormItem>
                  <FormLabel>{isEditing ? t("finance.invoiceFiles.form.pdfOptional") : t("finance.invoiceFiles.form.pdf")}</FormLabel>
                  <FormControl>
                    {!previewUrl ? (
                      <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                        <input
                          type="file"
                          accept=".pdf,application/pdf"
                          className="hidden"
                          onChange={handleFileChange}
                        />
                        <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                        <span className="text-sm text-muted-foreground">
                          {t("finance.invoiceFiles.form.clickToUpload")}
                        </span>
                      </label>
                    ) : (
                      <div className="relative flex items-center gap-3 p-3 border rounded-lg">
                        <FileText className="h-8 w-8 text-primary" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {uploadedFile?.name || record?.pdf_original_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {uploadedFile
                              ? `${(uploadedFile.size / 1024).toFixed(1)} KB`
                              : ""}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={handleRemoveFile}
                          className="rounded-full p-1 hover:bg-muted"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </FormControl>
                  {parseError && (
                    <p className="text-sm text-amber-600">{parseError}</p>
                  )}
                  {parseMutation.isPending && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t("finance.invoiceFiles.form.processing")}
                    </div>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="invoice_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.invoiceNumber")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.invoiceFiles.form.invoiceNumberPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="invoice_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.invoiceDate")}</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="invoice_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.invoiceAmount")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.invoiceFiles.form.amountPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tax_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.taxAmount")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.invoiceFiles.form.amountPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("finance.invoiceFiles.form.currency")}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t("finance.invoiceFiles.form.currencyPlaceholder")} />
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

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="buyer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.buyer")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.invoiceFiles.form.buyerPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="seller"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("finance.invoiceFiles.form.seller")}</FormLabel>
                    <FormControl>
                      <Input placeholder={t("finance.invoiceFiles.form.sellerPlaceholder")} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="invoice_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("finance.invoiceFiles.form.invoiceType")}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t("finance.invoiceFiles.form.invoiceTypePlaceholder")} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {INVOICE_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
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
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("finance.invoiceFiles.form.note")}</FormLabel>
                  <FormControl>
                    <Input placeholder={t("finance.invoiceFiles.form.notePlaceholder")} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} type="button">
            {t("finance.invoiceFiles.form.cancel")}
          </Button>
          <Button
            onClick={handleSaveDraft}
            disabled={createMutation.isPending || updateMutation.isPending}
            type="button"
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            {isEditing ? t("finance.invoiceFiles.form.saveEdit") : t("finance.invoiceFiles.form.saveDraft")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
