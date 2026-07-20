import { ArrowDown, ArrowUp, EllipsisVertical } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"

import type { DepartmentPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteDepartment from "./DeleteDepartment"
import EditDepartment from "./EditDepartment"

interface DepartmentActionsMenuProps {
  department: DepartmentPublic
  index: number
  total: number
  onMoveUp: (index: number) => void
  onMoveDown: (index: number) => void
}

export const DepartmentActionsMenu = ({
  department,
  index,
  total,
  onMoveUp,
  onMoveDown,
}: DepartmentActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const { t } = useTranslation()

  const move = (direction: -1 | 1) => {
    if (direction === -1) {
      onMoveUp(index)
    } else {
      onMoveDown(index)
    }
    setOpen(false)
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled={index === 0} onClick={() => move(-1)}>
          <ArrowUp />
          {t("okr.department.moveUp")}
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={index === total - 1}
          onClick={() => move(1)}
        >
          <ArrowDown />
          {t("okr.department.moveDown")}
        </DropdownMenuItem>
        <EditDepartment
          department={department}
          onSuccess={() => setOpen(false)}
        />
        <DeleteDepartment id={department.id} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
