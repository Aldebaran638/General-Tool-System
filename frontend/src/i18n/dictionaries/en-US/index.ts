import common from "./common"
import navigation from "./navigation"
import admin from "./admin"
import settings from "./settings"
import purchaseRecords from "./purchaseRecords"
import invoiceFiles from "./invoiceFiles"
import invoiceMatching from "./invoiceMatching"

const dict = {
  common,
  navigation,
  admin,
  settings,
  finance: {
    groupName: "Finance",
    purchaseRecords,
    invoiceFiles,
    invoiceMatching,
  },
}

export default dict
