/**
 * Contract Filler Tool Module
 *
 * Self-registers with the global tool registry on import.
 */

import { FileSignature } from "lucide-react"

import { registerTool } from "@/tools/registry"
import { ContractFillerPage } from "./components/ContractFillerPage"

registerTool({
  name: "contract_filler",
  group: "contracts",
  route: {
    path: "/contracts/contract-filler",
    title: "合同填充 - 工程承包合同",
    component: ContractFillerPage,
  },
  navigation: {
    title: "合同填充",
    titleKey: "contracts.contractFiller.title",
    icon: FileSignature,
    path: "/contracts/contract-filler",
    requiresSuperuser: false,
  },
})

export { ContractFillerPage }
export * from "./api"
export * from "./types"
export * from "./schemas"
