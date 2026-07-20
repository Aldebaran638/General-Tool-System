import { Trash2 } from "lucide-react"
import { useTranslation } from "react-i18next"

import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  const { t } = useTranslation()
  return (
    <div className="max-w-lg mt-2 rounded-xl border border-destructive/50 bg-destructive/5 p-5">
      <div className="flex items-start gap-3">
        <Trash2 className="h-5 w-5 text-destructive mt-0.5 shrink-0" />
        <div className="flex-1">
          <h3 className="font-semibold text-destructive">{t("deleteAccount.title")}</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("deleteAccount.description")}
          </p>
          <div className="mt-4">
            <DeleteConfirmation />
          </div>
        </div>
      </div>
    </div>
  )
}

export default DeleteAccount
