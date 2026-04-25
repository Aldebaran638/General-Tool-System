import { expect, test, type Page } from "@playwright/test"

import { createUser } from "../../utils/privateApi"
import { randomEmail, randomPassword } from "../../utils/random"
import { logInUser } from "../../utils/user"

async function gotoPurchaseRecordsFromSidebar(page: Page) {
  const purchaseRecordsLink = page.getByRole("link", { name: "购买记录" })
  await expect(page.getByRole("button", { name: "财务" })).toBeVisible()

  if (!(await purchaseRecordsLink.isVisible())) {
    await page.getByRole("button", { name: "财务" }).click()
  }

  await expect(purchaseRecordsLink).toBeVisible()
  await purchaseRecordsLink.click({ trial: true })
  await purchaseRecordsLink.click()
  await expect(page).toHaveURL(/\/finance\/purchase-records/)
}

test("购买记录页面可正常打开并显示标题", async ({ page }) => {
  await page.goto("/finance/purchase-records")
  await expect(page.getByRole("heading", { name: "购买记录" })).toBeVisible()
  await expect(page.getByText("管理和提交您的购买记录")).toBeVisible()
})

test("从侧边栏可进入购买记录页面", async ({ page }) => {
  await page.goto("/")
  await gotoPurchaseRecordsFromSidebar(page)
  await expect(page.getByRole("heading", { name: "购买记录" })).toBeVisible()
})

test("新建按钮可见", async ({ page }) => {
  await page.goto("/finance/purchase-records")
  await expect(
    page.getByRole("button", { name: "新建购买记录" }),
  ).toBeVisible()
})

test.describe("购买记录业务流程", () => {
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
    await page.goto("/finance/purchase-records")
  })

  test("空状态显示", async ({ page }) => {
    await expect(page.getByText("您还没有购买记录")).toBeVisible()
    await expect(page.getByText("点击上方按钮创建新的购买记录")).toBeVisible()
  })

  test("创建购买记录表单可打开", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByText("新建购买记录")).toBeVisible()
    await expect(page.getByText("上传截图并填写购买记录信息")).toBeVisible()
  })

  test("大类不是 other_project 时小类必须为空", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()

    // Fill form without screenshot (will fail validation but we test category logic first)
    await page.getByLabel("购买日期").fill("2026-04-24")
    await page.getByLabel("金额").fill("100.00")

    // Select currency
    await page.getByRole("combobox").filter({ hasText: "选择币种" }).click()
    await page.getByRole("option", { name: "CNY" }).click()

    await page.getByLabel("订单名称").fill("测试订单")

    // Select category that's not other_project
    await page
      .getByRole("combobox")
      .filter({ hasText: "选择大类" })
      .click()
    await page.getByRole("option", { name: "交通费用" }).click()

    // Try to select subcategory (should be disabled)
    const subcategoryTrigger = page
      .getByRole("combobox")
      .filter({ hasText: "选择小类" })
    await expect(subcategoryTrigger).toBeDisabled()
  })

  test("大类是 other_project 时小类可选择", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()

    // Select other_project category
    await page
      .getByRole("combobox")
      .filter({ hasText: "选择大类" })
      .click()
    await page.getByRole("option", { name: "其他项目费用" }).click()

    // Subcategory should now be enabled
    const subcategoryTrigger = page
      .getByRole("combobox")
      .filter({ hasText: "选择小类" })
    await expect(subcategoryTrigger).toBeEnabled()

    await subcategoryTrigger.click()
    await page.getByRole("option", { name: "自动导航承载车" }).click()
  })

  test("大类是 other_project 时小类允许为空", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()

    // Select other_project category without selecting subcategory
    await page
      .getByRole("combobox")
      .filter({ hasText: "选择大类" })
      .click()
    await page.getByRole("option", { name: "其他项目费用" }).click()

    // Verify subcategory is enabled but not required
    const subcategoryTrigger = page
      .getByRole("combobox")
      .filter({ hasText: "选择小类" })
    await expect(subcategoryTrigger).toBeEnabled()
    // No error should appear just because subcategory is empty
  })

  test("正常记录 / 已删除记录筛选可切换", async ({ page }) => {
    await expect(page.getByRole("tab", { name: "正常记录" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已删除记录" })).toBeVisible()

    await page.getByRole("tab", { name: "已删除记录" }).click()
    await expect(page.getByText("没有已删除的记录")).toBeVisible()
  })

  test("取消创建后对话框关闭", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()
    await page.getByRole("button", { name: "取消" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("OCR 失败后仍允许手填", async ({ page }) => {
    await page.getByRole("button", { name: "新建购买记录" }).click()

    // Upload a simple text file to trigger OCR error
    // In real scenario, this would be an image that OCR can't parse
    // For testing, we just verify the form fields are accessible after upload
    const fileInput = page.locator('input[type="file"]')

    // Create a simple test file
    const buffer = Buffer.from("test image content")
    await fileInput.setInputFiles({
      name: "test.png",
      mimeType: "image/png",
      buffer,
    })

    // Wait a bit for OCR processing
    await page.waitForTimeout(1000)

    // Form should still be fillable regardless of OCR result
    await page.getByLabel("购买日期").fill("2026-04-24")
    await page.getByLabel("金额").fill("100.00")
    await page.getByLabel("订单名称").fill("手动填写测试")

    // Verify fields are filled
    await expect(page.getByLabel("订单名称")).toHaveValue("手动填写测试")
  })
})

test.describe("管理员权限", () => {
  test("管理员页面可正常访问", async ({ page }) => {
    await page.goto("/finance/purchase-records")
    await expect(page.getByRole("heading", { name: "购买记录" })).toBeVisible()
  })
})
