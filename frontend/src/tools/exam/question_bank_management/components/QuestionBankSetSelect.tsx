import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  BookOpen,
  Loader2,
  Search,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

import { listSets } from "../api"
import { listExamCategories } from "../../category_management/api"
import type { ImportMode, QuestionBankSet } from "../types"

interface QuestionBankSetSelectProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (set: QuestionBankSet, mode: ImportMode) => void
  isLoading?: boolean
}

export function QuestionBankSetSelect({
  open,
  onOpenChange,
  onConfirm,
  isLoading,
}: QuestionBankSetSelectProps) {
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null)
  const [mode, setMode] = useState<ImportMode>("append")

  const categoriesQuery = useQuery({
    queryKey: ["examCategories"],
    queryFn: listExamCategories,
    enabled: open,
  })
  const categories = categoriesQuery.data?.data ?? []

  const setsQuery = useQuery({
    queryKey: ["questionBankSets", search, categoryFilter],
    queryFn: () =>
      listSets({
        q: search || undefined,
        category_id:
          categoryFilter === "all" ? undefined : Number(categoryFilter),
      }),
    enabled: open,
  })

  const sets = setsQuery.data?.data ?? []
  const selectedSet = sets.find((s) => s.id === selectedSetId)

  function handleConfirm() {
    if (selectedSet) {
      onConfirm(selectedSet, mode)
    }
  }

  function handleOpenChange(next: boolean) {
    if (!next) {
      setSelectedSetId(null)
      setMode("append")
    }
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>从题库导入</DialogTitle>
          <DialogDescription>
            选择题库并指定导入方式，将题目导入当前试卷。
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索题库名称…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="全部分类" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部分类</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border h-[240px] overflow-y-auto">
            {setsQuery.isLoading && (
              <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                加载中…
              </div>
            )}
            {!setsQuery.isLoading && sets.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-sm text-muted-foreground">
                <BookOpen className="h-8 w-8 mb-2" />
                暂无匹配题库
              </div>
            )}
            {!setsQuery.isLoading &&
              sets.map((set) => {
                const isSelected = selectedSetId === set.id
                const categoryName =
                  categories.find((c) => c.id === set.category_id)?.name ??
                  "无分类"
                return (
                  <button
                    key={set.id}
                    type="button"
                    onClick={() => setSelectedSetId(set.id)}
                    className={`w-full text-left px-4 py-3 border-b border-border/50 last:border-b-0 transition-colors ${
                      isSelected ? "bg-muted" : "hover:bg-muted/50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{set.name}</span>
                      {isSelected && (
                        <Badge variant="default">已选择</Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <span>{categoryName}</span>
                    </div>
                    {set.description && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                        {set.description}
                      </p>
                    )}
                  </button>
                )
              })}
          </div>

          <div className="grid gap-2">
            <Label>导入方式</Label>
            <RadioGroup
              value={mode}
              onValueChange={(v) => setMode(v as ImportMode)}
              className="flex flex-col gap-2"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="append" id="mode-append" />
                <Label htmlFor="mode-append" className="font-normal cursor-pointer">
                  追加导入（保留现有题目并追加题库题目）
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="overwrite" id="mode-overwrite" />
                <Label htmlFor="mode-overwrite" className="font-normal cursor-pointer">
                  覆盖导入（清空现有题目并替换为题库题目）
                </Label>
              </div>
            </RadioGroup>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!selectedSet || isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            确认导入
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
