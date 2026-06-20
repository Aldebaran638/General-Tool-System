import { createFileRoute } from "@tanstack/react-router"

import { toolRegistry } from "@/tools/registry"

const tool = toolRegistry.getTool("contract_filler")
const ContractFillerPage = tool?.route.component

export const Route = createFileRoute("/_layout/contracts/contract-filler")({
  component: ContractFillerRoute,
  head: () => ({
    meta: [
      {
        title: tool?.route.title || "合同填充",
      },
    ],
  }),
})

function ContractFillerRoute() {
  if (!ContractFillerPage) {
    return null
  }

  return <ContractFillerPage />
}
