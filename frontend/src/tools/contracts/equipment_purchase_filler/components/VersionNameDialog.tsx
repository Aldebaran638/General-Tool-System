import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface VersionNameDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (name: string) => void
  defaultName?: string
  title?: string
  description?: string
  label?: string
  placeholder?: string
  confirmText?: string
}

export function VersionNameDialog({
  open,
  onOpenChange,
  onConfirm,
  defaultName = "",
  title = "保存版本",
  description = "输入版本名称，方便后续查找和导出。",
  label = "版本名称",
  placeholder = "例如：张三合同2025",
  confirmText = "保存",
}: VersionNameDialogProps) {
  const [name, setName] = useState(defaultName)

  const handleConfirm = () => {
    if (name.trim()) {
      onConfirm(name.trim())
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="version-name" className="text-right">
              {label}
            </Label>
            <Input
              id="version-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={placeholder}
              className="col-span-3"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleConfirm()
              }}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleConfirm} disabled={!name.trim()}>
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
