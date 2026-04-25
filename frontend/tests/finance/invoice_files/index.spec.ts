import { expect, test, type Page } from "@playwright/test"

import { createUser } from "../../utils/privateApi"
import { randomEmail, randomPassword } from "../../utils/random"
import { logInUser } from "../../utils/user"

async function gotoInvoiceFilesFromSidebar(page: Page) {
  const invoiceFilesLink = page.getByRole("link", { name: "发票文件" })
  await expect(page.getByRole("button", { name: "财务" })).toBeVisible()

  if (!(await invoiceFilesLink.isVisible())) {
    await page.getByRole("button", { name: "财务" }).click()
  }

  await expect(invoiceFilesLink).toBeVisible()
  await invoiceFilesLink.click({ trial: true })
  await invoiceFilesLink.click()
  await expect(page).toHaveURL(/\/finance\/invoice-files/)
}

test("发票文件页面可正常打开并显示标题", async ({ page }) => {
  await page.goto("/finance/invoice-files")
  await expect(page.getByRole("heading", { name: "发票文件" })).toBeVisible()
  await expect(page.getByText("管理和确认您的发票文件")).toBeVisible()
})

test("从侧边栏可进入发票文件页面", async ({ page }) => {
  await page.goto("/")
  await gotoInvoiceFilesFromSidebar(page)
  await expect(page.getByRole("heading", { name: "发票文件" })).toBeVisible()
})

test("新建按钮可见", async ({ page }) => {
  await page.goto("/finance/invoice-files")
  await expect(
    page.getByRole("button", { name: "新建发票" }),
  ).toBeVisible()
})

test.describe("发票文件业务流程", () => {
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
    await page.goto("/finance/invoice-files")
  })

  test("空状态显示", async ({ page }) => {
    await expect(page.getByText("您还没有发票文件")).toBeVisible()
    await expect(page.getByText("点击上方按钮创建新的发票文件")).toBeVisible()
  })

  test("创建发票文件表单可打开", async ({ page }) => {
    await page.getByRole("button", { name: "新建发票" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByText("新建发票文件")).toBeVisible()
    await expect(page.getByText("上传 PDF 发票并填写相关信息")).toBeVisible()
  })

  test("正常记录 / 已删除记录筛选可切换", async ({ page }) => {
    await expect(page.getByRole("tab", { name: "正常记录" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已删除记录" })).toBeVisible()

    await page.getByRole("tab", { name: "已删除记录" }).click()
    await expect(page.getByText("没有已删除的发票")).toBeVisible()
  })

  test("取消创建后对话框关闭", async ({ page }) => {
    await page.getByRole("button", { name: "新建发票" }).click()
    await page.getByRole("button", { name: "取消" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("PDF 解析失败后仍允许手填", async ({ page }) => {
    await page.getByRole("button", { name: "新建发票" }).click()

    const fileInput = page.locator('input[type="file"]')

    // Upload a simple text file to trigger PDF parse error
    const buffer = Buffer.from("not a valid pdf content")
    await fileInput.setInputFiles({
      name: "test.txt",
      mimeType: "text/plain",
      buffer,
    })

    // Wait a bit for PDF processing
    await page.waitForTimeout(1000)

    // Form should still be fillable regardless of parse result
    await page.getByLabel("发票号码").fill("INV-2026-001")
    await page.getByLabel("发票金额").fill("1000.00")
    await page.getByLabel("购买方").fill("测试公司")
    await page.getByLabel("销售方").fill("供应商 A")

    // Verify fields are filled
    await expect(page.getByLabel("发票号码")).toHaveValue("INV-2026-001")
  })
})

test.describe("管理员权限", () => {
  test("管理员页面可正常访问", async ({ page }) => {
    await page.goto("/finance/invoice-files")
    await expect(page.getByRole("heading", { name: "发票文件" })).toBeVisible()
  })
})
