import { z } from "zod"

export interface ContractFillerFormValues {
  version_name: string
  description?: string
  field_values: Record<string, string>
}

export function createContractFillerSchemas(t: (key: string) => string) {
  const versionNameSchema = z
    .string()
    .min(1, { message: t("contracts.contractFiller.validation.versionNameRequired") })

  return { versionNameSchema }
}
