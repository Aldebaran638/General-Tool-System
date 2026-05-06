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

async function gotoReimbursementExportsFromSidebar(page: Page) {
  const link = page.getByRole("link", { name: "报销导出" })
  await expect(page.getByRole("button", { name: "财务" })).toBeVisible()

  if (!(await link.isVisible())) {
    await page.getByRole("button", { name: "财务" }).click()
  }

  await expect(link).toBeVisible()
  await link.evaluate((el: HTMLElement) => el.click())
  await expect(page).toHaveURL(/\/finance\/reimbursement-exports/)
}

test.describe("Round 008 / reimbursement_exports 前端", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/")
    await page.evaluate(() => localStorage.setItem("app_locale", "zh-CN"))
    await page.reload()
  })

  test("报销导出页面可正常打开并显示标题", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await expect(
      page.getByRole("heading", { name: "报销导出" }),
    ).toBeVisible()
    await expect(
      page.getByText("导出已批准的购买记录并生成 Excel 报销文件"),
    ).toBeVisible()
  })

  test("从侧边栏可进入报销导出页面", async ({ page }) => {
    await page.goto("/")
    await gotoReimbursementExportsFromSidebar(page)
    await expect(
      page.getByRole("heading", { name: "报销导出" }),
    ).toBeVisible()
  })

  test("可导出记录 / 导出历史 两个 tab 都存在", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await expect(page.getByRole("tab", { name: "可导出记录" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "导出历史" })).toBeVisible()
  })

  test("可导出记录 tab 默认显示空状态", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await expect(page.getByText("暂无可导出的记录")).toBeVisible()
    await expect(
      page.getByText("请确保有已批准且已匹配发票的购买记录"),
    ).toBeVisible()
  })

  test("导出历史 tab 切换可见空状态文案", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await page.getByRole("tab", { name: "导出历史" }).click()
    await expect(page.getByText("暂无导出历史")).toBeVisible()
    await expect(
      page.getByText("在「可导出记录」中选择记录并生成导出后，将在此处显示"),
    ).toBeVisible()
  })

  test("设置按钮可见", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await expect(
      page.getByRole("button", { name: "导出设置" }),
    ).toBeVisible()
  })

  test("英文 i18n 接入正确", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await setLocale(page, "en-US")

    await expect(
      page.getByRole("heading", { name: "Reimbursement Export" }),
    ).toBeVisible()
    await expect(page.getByRole("tab", { name: "Exportable Records" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "Export History" })).toBeVisible()
  })

  test("繁体中文 i18n 接入正确", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await setLocale(page, "zh-TW")

    await expect(
      page.getByRole("heading", { name: "報銷導出" }),
    ).toBeVisible()
    await expect(page.getByRole("tab", { name: "可導出記錄" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "導出歷史" })).toBeVisible()
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
    await setLocale(page, "zh-CN")
  })

  test("普通用户侧边栏看不到报销导出入口", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByRole("button", { name: "财务" })).toBeVisible()
    await page.getByRole("button", { name: "财务" }).click()
    await expect(
      page.getByRole("link", { name: "报销导出" }),
    ).not.toBeVisible()
  })

  test("普通用户直接访问报销导出页面返回权限不足", async ({ page }) => {
    await page.goto("/finance/reimbursement-exports")
    await expect(page.getByText("权限不足")).toBeVisible()
    await expect(page.getByText("报销导出功能仅限管理员访问")).toBeVisible()
  })
})
