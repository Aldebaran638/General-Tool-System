import common from "./common"
import navigation from "./navigation"
import admin from "./admin"
import settings from "./settings"
import auth from "./auth"
import purchaseRecords from "./purchaseRecords"
import invoiceFiles from "./invoiceFiles"
import invoiceMatching from "./invoiceMatching"
import reimbursementExports from "./reimbursementExports"

const dict = {
  common,
  navigation,
  admin,
  settings,
  auth,
  finance: {
    groupName: "財務",
    purchaseRecords,
    invoiceFiles,
    invoiceMatching,
    invoiceMatchAudit: {
      title: "發票匹配審核",
    },
    reimbursementExports,
  },
}

export default dict
