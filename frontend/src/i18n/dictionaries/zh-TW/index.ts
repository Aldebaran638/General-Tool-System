import common from "./common"
import navigation from "./navigation"
import admin from "./admin"
import settings from "./settings"
import purchaseRecords from "./purchaseRecords"
import invoiceFiles from "./invoiceFiles"
import invoiceMatching from "./invoiceMatching"
import reimbursementExports from "./reimbursementExports"

const dict = {
  common,
  navigation,
  admin,
  settings,
  finance: {
    groupName: "財務",
    purchaseRecords,
    invoiceFiles,
    invoiceMatching,
    reimbursementExports,
  },
}

export default dict
