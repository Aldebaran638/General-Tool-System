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
  invoiceFileFormSchema,
  type InvoiceFileFormValues,
  INVOICE_TYPES,
  CURRENCIES,
} from "../schemas"
import {
  useCreateInvoiceFileMutation,
  useUpdateInvoiceFileMutation,
  useParsePreviewMutation,
} from "../hooks/useInvoiceFiles"

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
        setParseError("PDF 解析失败，请手动填写发票信息")
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
      toast.error("请上传 PDF 文件")
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
            {isEditing ? "编辑发票文件" : "新建发票文件"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "修改发票文件信息"
              : "上传 PDF 发票并填写相关信息"}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4">
            {/* PDF Upload */}
            <FormField
              control={form.control}
              name="pdf"
              render={() => (
                <FormItem>
                  <FormLabel>PDF 发票 {isEditing ? "(可选)" : ""}</FormLabel>
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
                          点击上传 PDF 发票
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
                      正在解析 PDF...
                    </div>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Invoice Number & Date */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="invoice_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>发票号码</FormLabel>
                    <FormControl>
                      <Input placeholder="请输入发票号码" {...field} />
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
                    <FormLabel>发票日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Amount & Tax */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="invoice_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>发票金额</FormLabel>
                    <FormControl>
                      <Input placeholder="0.00" {...field} />
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
                    <FormLabel>税额（可选）</FormLabel>
                    <FormControl>
                      <Input placeholder="0.00" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Currency */}
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>币种</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
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

            {/* Buyer & Seller */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="buyer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>购买方</FormLabel>
                    <FormControl>
                      <Input placeholder="请输入购买方" {...field} />
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
                    <FormLabel>销售方</FormLabel>
                    <FormControl>
                      <Input placeholder="请输入销售方" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Invoice Type */}
            <FormField
              control={form.control}
              name="invoice_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>发票类型</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择发票类型" />
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

            {/* Note */}
            <FormField
              control={form.control}
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>备注（可选）</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入备注" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} type="button">
            取消
          </Button>
          <Button
            onClick={handleSaveDraft}
            disabled={createMutation.isPending || updateMutation.isPending}
            type="button"
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            {isEditing ? "保存修改" : "保存草稿"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
