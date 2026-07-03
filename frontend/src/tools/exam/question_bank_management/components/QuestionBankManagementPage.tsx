import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  BookOpen,
  Loader2,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

import { listSets, createSet, updateSet, deleteSet } from "../api"
import { listExamCategories } from "../../category_management/api"
import type { QuestionBankSet } from "../types"

function fmtDate(s: string | null): string {
  if (!s) return "—"
  return new Date(s).toLocaleString("zh-CN", { hour12: false })
}

interface SetFormData {
  name: string
  description: string
  category_id: string
}

function emptyForm(): SetFormData {
  return { name: "", description: "", category_id: "none" }
}

function formToCreate(data: SetFormData): {
  name: string
  description?: string
  category_id?: number | null
} {
  return {
    name: data.name.trim(),
    description: data.description.trim() || undefined,
    category_id: data.category_id === "none" ? null : Number(data.category_id),
  }
}

export function QuestionBankManagementPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [deleteTarget, setDeleteTarget] = useState<QuestionBankSet | null>(null)

  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<SetFormData>(emptyForm())

  const [editTarget, setEditTarget] = useState<QuestionBankSet | null>(null)
  const [editForm, setEditForm] = useState<SetFormData>(emptyForm())

  const categoriesQuery = useQuery({
    queryKey: ["examCategories"],
    queryFn: listExamCategories,
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
  })

  const createMutation = useMutation({
    mutationFn: createSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSets"] })
      setCreateOpen(false)
      setCreateForm(emptyForm())
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReturnType<typeof formToCreate> }) =>
      updateSet(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSets"] })
      setEditTarget(null)
      setEditForm(emptyForm())
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSet(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questionBankSets"] })
      setDeleteTarget(null)
    },
  })

  const sets = setsQuery.data?.data ?? []

  function openCreate() {
    setCreateForm(emptyForm())
    setCreateOpen(true)
  }

  function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!createForm.name.trim()) return
    createMutation.mutate(formToCreate(createForm))
  }

  function openEdit(set: QuestionBankSet) {
    setEditTarget(set)
    setEditForm({
      name: set.name,
      description: set.description ?? "",
      category_id: set.category_id?.toString() ?? "none",
    })
  }

  function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!editTarget || !editForm.name.trim()) return
    updateMutation.mutate({ id: editTarget.id, data: formToCreate(editForm) })
  }

  function handleDelete(set: QuestionBankSet) {
    setDeleteTarget(set)
  }

  function confirmDelete() {
    if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">题库管理</h1>
          <p className="text-muted-foreground">
            管理预置题库，供组卷时快速导入
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建题库
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative max-w-sm flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索题库名称…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-40">
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

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>题库名称</TableHead>
              <TableHead>分类</TableHead>
              <TableHead>更新时间</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {setsQuery.isLoading && (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="text-center text-muted-foreground py-8"
                >
                  <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                  加载中…
                </TableCell>
              </TableRow>
            )}
            {!setsQuery.isLoading && sets.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-12">
                  <div className="flex flex-col items-center gap-3">
                    <div className="rounded-full bg-muted p-4">
                      <BookOpen className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">暂无题库</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        点击"新建题库"创建第一个题库
                      </p>
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            )}
            {sets.map((set) => (
              <TableRow
                key={set.id}
                className="group transition-colors hover:bg-muted/50"
              >
                <TableCell className="font-medium">
                  <button
                    className="hover:underline text-left group-hover:text-primary transition-colors"
                    onClick={() =>
                      navigate({ to: `/question-bank-management/${set.id}` })
                    }
                  >
                    {set.name}
                  </button>
                  {set.description && (
                    <p className="text-xs text-muted-foreground font-normal mt-0.5 line-clamp-1">
                      {set.description}
                    </p>
                  )}
                </TableCell>
                <TableCell className="text-sm">
                  {categories.find((c) => c.id === set.category_id)?.name ?? "—"}
                </TableCell>
                <TableCell className="text-sm">
                  {fmtDate(set.updated_at)}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() =>
                          navigate({ to: `/question-bank-management/${set.id}` })
                        }
                      >
                        <BookOpen className="mr-2 h-4 w-4" />
                        管理题目
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openEdit(set)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        编辑
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-red-600"
                        onClick={() => handleDelete(set)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        删除
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>新建题库</DialogTitle>
            <DialogDescription>创建一个新的预置题库。</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit} className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label htmlFor="create-name">题库名称</Label>
              <Input
                id="create-name"
                value={createForm.name}
                onChange={(e) =>
                  setCreateForm({ ...createForm, name: e.target.value })
                }
                placeholder="输入题库名称"
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-desc">描述（可选）</Label>
              <Textarea
                id="create-desc"
                value={createForm.description}
                onChange={(e) =>
                  setCreateForm({ ...createForm, description: e.target.value })
                }
                placeholder="输入题库描述"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-category">分类（可选）</Label>
              <Select
                value={createForm.category_id}
                onValueChange={(v) =>
                  setCreateForm({ ...createForm, category_id: v })
                }
              >
                <SelectTrigger id="create-category">
                  <SelectValue placeholder="选择分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">无分类</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {createMutation.isError && (
              <p className="text-sm text-red-600">
                {(createMutation.error as Error).message}
              </p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                创建
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      <Dialog open={!!editTarget} onOpenChange={() => setEditTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>编辑题库</DialogTitle>
            <DialogDescription>修改题库基本信息。</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">题库名称</Label>
              <Input
                id="edit-name"
                value={editForm.name}
                onChange={(e) =>
                  setEditForm({ ...editForm, name: e.target.value })
                }
                placeholder="输入题库名称"
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-desc">描述（可选）</Label>
              <Textarea
                id="edit-desc"
                value={editForm.description}
                onChange={(e) =>
                  setEditForm({ ...editForm, description: e.target.value })
                }
                placeholder="输入题库描述"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-category">分类（可选）</Label>
              <Select
                value={editForm.category_id}
                onValueChange={(v) =>
                  setEditForm({ ...editForm, category_id: v })
                }
              >
                <SelectTrigger id="edit-category">
                  <SelectValue placeholder="选择分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">无分类</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {updateMutation.isError && (
              <p className="text-sm text-red-600">
                {(updateMutation.error as Error).message}
              </p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditTarget(null)}
              >
                取消
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除题库"{deleteTarget?.name}"吗？题库内的所有题目也将被删除，此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
