import common from "./common"
import navigation from "./navigation"
import admin from "./admin"
import settings from "./settings"
import purchaseRecords from "./purchaseRecords"
import invoiceFiles from "./invoiceFiles"

const dict = {
  common,
  navigation,
  admin,
  settings,
  finance: {
    groupName: "財務",
    purchaseRecords,
    invoiceFiles,
  },
}

export default dict
