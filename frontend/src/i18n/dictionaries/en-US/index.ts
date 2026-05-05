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
    groupName: "Finance",
    purchaseRecords,
    invoiceFiles,
    invoiceMatching,
    reimbursementExports,
  },
}

export default dict
