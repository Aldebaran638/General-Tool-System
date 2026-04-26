import { expect, test, type Page } from "@playwright/test"

import { createUser } from "../../utils/privateApi"
import { randomEmail, randomPassword } from "../../utils/random"
import { logInUser } from "../../utils/user"

async function setLocale(
  page: Page,
  locale: "zh-CN" | "en-US" | "zh-TW",
): Promise<void> {
  await page.evaluate((l) => localStorage.setItem("app_locale", l), locale)
  await page.reload()
}

async function gotoInvoiceMatchingFromSidebar(page: Page) {
  const matchingLink = page.getByRole("link", { name: "发票匹配" })
  await expect(page.getByRole("button", { name: "财务" })).toBeVisible()

  if (!(await matchingLink.isVisible())) {
    await page.getByRole("button", { name: "财务" }).click()
  }

  await expect(matchingLink).toBeVisible()
  await matchingLink.click()
  await expect(page).toHaveURL(/\/finance\/invoice-matching/)
}

test.describe("Round 005 / invoice_matching 前端", () => {
  test("发票匹配页面可正常打开并显示标题", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await expect(
      page.getByRole("heading", { name: "发票匹配" }),
    ).toBeVisible()
    await expect(
      page.getByText("将购买记录与已确认发票进行关联"),
    ).toBeVisible()
  })

  test("从侧边栏可进入发票匹配页面", async ({ page }) => {
    await page.goto("/")
    await gotoInvoiceMatchingFromSidebar(page)
    await expect(
      page.getByRole("heading", { name: "发票匹配" }),
    ).toBeVisible()
  })

  test("待匹配 / 已匹配 / 需复核 / 已取消 四个 tab 都存在", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await expect(page.getByRole("tab", { name: "待匹配" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已匹配" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "需复核" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已取消" })).toBeVisible()
  })

  test("已匹配 tab 切换可见空状态文案", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await page.getByRole("tab", { name: "已匹配" }).click()
    // 默认管理员且未创建匹配，应该看到空状态文案
    await expect(page.getByText("暂无已匹配的记录")).toBeVisible()
  })

  test("需复核 tab 切换可见空状态文案", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await page.getByRole("tab", { name: "需复核" }).click()
    await expect(page.getByText("暂无需复核的匹配")).toBeVisible()
  })

  test("已取消 tab 切换可见空状态文案", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await page.getByRole("tab", { name: "已取消" }).click()
    await expect(page.getByText("暂无已取消的匹配")).toBeVisible()
  })

  test("汇总卡片显示已匹配 / 需复核 / 已取消 / 待匹配 / 可匹配发票", async ({
    page,
  }) => {
    await page.goto("/finance/invoice-matching")
    await expect(page.getByTestId("summary-confirmed")).toBeVisible()
    await expect(page.getByTestId("summary-needs-review")).toBeVisible()
    await expect(page.getByTestId("summary-cancelled")).toBeVisible()
    await expect(page.getByTestId("summary-unmatched")).toBeVisible()
    await expect(page.getByTestId("summary-available")).toBeVisible()
  })

  test("管理员登录时显示只读提示，不展示代用户操作按钮", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await expect(
      page.getByText(
        "管理员模式：仅查看，不可代用户确认 / 取消 / 重新确认。",
      ),
    ).toBeVisible()
  })

  test("英文 i18n 接入正确", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await setLocale(page, "en-US")

    await expect(
      page.getByRole("heading", { name: "Invoice Matching" }),
    ).toBeVisible()
    await expect(page.getByRole("tab", { name: "Unmatched" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "Matched" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "Needs Review" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "Cancelled" })).toBeVisible()
  })

  test("繁体中文 i18n 接入正确", async ({ page }) => {
    await page.goto("/finance/invoice-matching")
    await setLocale(page, "zh-TW")

    await expect(
      page.getByRole("heading", { name: "發票匹配" }),
    ).toBeVisible()
    await expect(page.getByRole("tab", { name: "需複核" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已取消" })).toBeVisible()
  })
})

test.describe("普通用户视角", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  let email: string
  let password: string

  test.beforeAll(async () => {
    email = randomEmail()
    password = randomPassword()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/finance/invoice-matching")
  })

  test("普通用户看不到管理员只读提示", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "发票匹配" }),
    ).toBeVisible()
    await expect(
      page.getByText(
        "管理员模式：仅查看，不可代用户确认 / 取消 / 重新确认。",
      ),
    ).not.toBeVisible()
  })

  test("普通用户在待匹配 tab 看到空状态", async ({ page }) => {
    await expect(page.getByText("暂无待匹配的购买记录")).toBeVisible()
  })

  test("汇总卡片对普通用户也可见", async ({ page }) => {
    await expect(page.getByTestId("summary-unmatched")).toBeVisible()
    await expect(page.getByTestId("summary-available")).toBeVisible()
  })
})
