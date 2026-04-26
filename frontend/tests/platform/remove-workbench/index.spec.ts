import { expect, test, type Page } from "@playwright/test"

import { randomEmail, randomPassword } from "../../utils/random"

async function setLocale(
  page: Page,
  locale: "zh-CN" | "en-US" | "zh-TW",
): Promise<void> {
  await page.evaluate((l) => localStorage.setItem("app_locale", l), locale)
  await page.reload()
}

test.describe("Round 006 / remove_workbench 收尾验证", () => {
  test("zh-CN 侧边栏不再显示 工作台 / 项目管理", async ({ page }) => {
    await page.goto("/settings")
    await setLocale(page, "zh-CN")

    await expect(
      page.getByRole("button", { name: "工作台", exact: true }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("link", { name: "项目管理", exact: true }),
    ).toHaveCount(0)
  })

  test("en-US 侧边栏不再显示 Workbench / Project Management", async ({
    page,
  }) => {
    await page.goto("/settings")
    await setLocale(page, "en-US")

    await expect(
      page.getByRole("button", { name: "Workbench", exact: true }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("link", { name: "Project Management", exact: true }),
    ).toHaveCount(0)
  })

  test("zh-TW 侧边栏不再显示 工作台 / 项目管理 的繁体写法", async ({
    page,
  }) => {
    await page.goto("/settings")
    await setLocale(page, "zh-TW")

    await expect(
      page.getByRole("button", { name: "工作台", exact: true }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("link", { name: "項目管理", exact: true }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("link", { name: "專案管理", exact: true }),
    ).toHaveCount(0)
  })

  test("/items 路由不再渲染项目管理页面", async ({ page }) => {
    await page.goto("/items")

    // 项目管理页面专属元素必须不存在（路由已在 Round 006 删除）
    await expect(
      page.getByRole("button", { name: /^Add Item$/i }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("button", { name: /^添加项目$/ }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("heading", { name: /Items Management/i }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("heading", { name: "项目管理", exact: true }),
    ).toHaveCount(0)
  })

  test("用户删除确认文案不再包含 items（en-US）", async ({ page }) => {
    await page.goto("/settings")
    await setLocale(page, "en-US")

    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()

    await page.getByRole("button", { name: "Add User" }).click()
    await page.getByPlaceholder("Email").fill(email)
    await page.getByPlaceholder("Password").first().fill(password)
    await page.getByPlaceholder("Password").last().fill(password)
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("User created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await userRow.getByRole("button").click()
    await page.getByRole("menuitem", { name: "Delete User" }).click()

    const dialog = page.getByRole("dialog")
    try {
      await expect(dialog).toBeVisible()
      await expect(dialog).toContainText(
        "Data associated with this user will be permanently deleted",
      )
      await expect(dialog).not.toContainText(/items/i)
    } finally {
      // 清理：必须确认删除刚刚创建的测试用户，避免污染数据库
      if (await dialog.isVisible().catch(() => false)) {
        await dialog
          .getByRole("button", { name: "Delete User", exact: true })
          .click()
        await expect(page.getByText("User deleted successfully")).toBeVisible()
        await expect(userRow).not.toBeVisible()
      }
    }
  })

  test("用户删除确认文案不再包含 项目（zh-CN）", async ({ page }) => {
    await page.goto("/settings")
    await setLocale(page, "zh-CN")

    await page.goto("/admin")

    const email = randomEmail()
    const password = randomPassword()

    await page.getByRole("button", { name: "添加用户" }).click()
    await page.getByPlaceholder("邮箱").fill(email)
    await page.getByPlaceholder("密码").first().fill(password)
    await page.getByPlaceholder("密码").last().fill(password)
    await page.getByRole("button", { name: "保存" }).click()
    await expect(page.getByText("用户创建成功")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    const userRow = page.getByRole("row").filter({ hasText: email })
    await userRow.getByRole("button").click()
    await page.getByRole("menuitem", { name: "删除用户" }).click()

    const dialog = page.getByRole("dialog")
    try {
      await expect(dialog).toBeVisible()
      await expect(dialog).toContainText("该用户相关数据将被永久删除")
      await expect(dialog).not.toContainText("项目")
    } finally {
      // 清理：必须确认删除刚刚创建的测试用户，避免污染数据库
      if (await dialog.isVisible().catch(() => false)) {
        await dialog
          .getByRole("button", { name: "删除用户", exact: true })
          .click()
        await expect(page.getByText("用户删除成功")).toBeVisible()
        await expect(userRow).not.toBeVisible()
      }
    }
  })
})
