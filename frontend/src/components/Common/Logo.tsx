import { Link } from "@tanstack/react-router"
import { Receipt } from "lucide-react"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

const PRODUCT_NAME = "发票管理系统"

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const renderFull = (extraCls?: string) => (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-semibold tracking-tight",
        extraCls,
        className,
      )}
    >
      <Receipt className="h-[1.2em] w-[1.2em] shrink-0" aria-hidden="true" />
      <span>{PRODUCT_NAME}</span>
    </span>
  )

  const renderIcon = (extraCls?: string) => (
    <Receipt
      className={cn("size-5", extraCls, className)}
      aria-label={PRODUCT_NAME}
    />
  )

  const content =
    variant === "responsive" ? (
      <>
        {renderFull("group-data-[collapsible=icon]:hidden")}
        {renderIcon("hidden group-data-[collapsible=icon]:block")}
      </>
    ) : variant === "full" ? (
      renderFull()
    ) : (
      renderIcon()
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
