import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Plus, Pencil, Trash2, Save, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import {
  listExamCategories,
  createExamCategory,
  updateExamCategory,
  deleteExamCategory,
} from "../api"
import type { ExamCategory } from "../api"

export function ExamCategoryManagementPage() {
  const queryClient = useQueryClient()
  const [newName, setNewName] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState("")

  const categoriesQuery = useQuery({
    queryKey: ["examCategories"],
    queryFn: listExamCategories,
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => createExamCategory({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["examCategories"] })
      setNewName("")
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      updateExamCategory(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["examCategories"] })
      setEditingId(null)
      setEditingName("")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteExamCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["examCategories"] })
    },
  })

  const categories = categoriesQuery.data?.data ?? []

  function handleCreate() {
    if (!newName.trim()) return
    createMutation.mutate(newName.trim())
  }

  function handleUpdate() {
    if (editingId === null || !editingName.trim()) return
    updateMutation.mutate({ id: editingId, name: editingName.trim() })
  }

  function handleDelete(id: number) {
    if (confirm("确定删除此分类？有关联考试时无法删除。")) {
      deleteMutation.mutate(id)
    }
  }

  function startEditing(category: ExamCategory) {
    setEditingId(category.id)
    setEditingName(category.name)
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">试卷分类管理</h1>
        <p className="text-muted-foreground">管理考试试卷的分类</p>
      </div>

      {/* 新增分类 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">新增分类</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="输入分类名称"
              value={newName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setNewName(e.target.value)
              }
              onKeyDown={(e: React.KeyboardEvent) =>
                e.key === "Enter" && handleCreate()
              }
            />
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-2 h-4 w-4" />
              )}
              新增
            </Button>
          </div>
          {createMutation.isError && (
            <p className="text-sm text-red-600 mt-2">
              {(createMutation.error as Error).message}
            </p>
          )}
        </CardContent>
      </Card>

      {/* 分类列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">分类列表</CardTitle>
        </CardHeader>
        <CardContent>
          {categoriesQuery.isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : categories.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暂无分类
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>排序</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="w-24">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {categories.map((category) => (
                  <TableRow key={category.id}>
                    <TableCell>{category.id}</TableCell>
                    <TableCell>
                      {editingId === category.id ? (
                        <Input
                          value={editingName}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setEditingName(e.target.value)
                          }
                          onKeyDown={(e: React.KeyboardEvent) =>
                            e.key === "Enter" && handleUpdate()
                          }
                          className="h-8"
                        />
                      ) : (
                        category.name
                      )}
                    </TableCell>
                    <TableCell>{category.sort_order}</TableCell>
                    <TableCell>
                      {category.created_at
                        ? new Date(category.created_at).toLocaleString("zh-CN")
                        : "—"}
                    </TableCell>
                    <TableCell>
                      {editingId === category.id ? (
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={handleUpdate}
                            disabled={updateMutation.isPending}
                          >
                            <Save className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setEditingId(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => startEditing(category)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-400"
                            onClick={() => handleDelete(category.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
