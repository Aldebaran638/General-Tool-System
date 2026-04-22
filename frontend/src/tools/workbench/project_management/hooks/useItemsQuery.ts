import { useSuspenseQuery } from "@tanstack/react-query"

import { getItemsQueryOptions } from "../api"

export function useItemsQuery() {
  return useSuspenseQuery(getItemsQueryOptions())
}