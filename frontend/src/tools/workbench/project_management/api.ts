import { ItemsService } from "@/client"

import type { ItemCreate, ItemUpdate } from "./types"

export const itemsQueryKey = ["items"] as const

export function getItemsQueryOptions() {
  return {
    queryFn: () => ItemsService.readItems({ skip: 0, limit: 100 }),
    queryKey: itemsQueryKey,
  }
}

export function createItem(requestBody: ItemCreate) {
  return ItemsService.createItem({ requestBody })
}

export function updateItem(id: string, requestBody: ItemUpdate) {
  return ItemsService.updateItem({ id, requestBody })
}

export function deleteItem(id: string) {
  return ItemsService.deleteItem({ id })
}