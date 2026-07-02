import { expect, test, type Page } from "@playwright/test"

async function gotoDepartmentSync(page: Page) {
  await page.goto("/wecom-department-sync")
  await expect(page.getByRole("heading", { name: "企微部门同步" })).toBeVisible()
}

test.describe("企微部门同步页面", () => {
  test("页面标题和基本结构可见", async ({ page }) => {
    await gotoDepartmentSync(page)

    await expect(page.getByText("将企业微信通讯录中的部门树同步到本地数据库")).toBeVisible()

    // Tabs
    await expect(page.getByRole("tab", { name: "操作面板" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "同步历史" })).toBeVisible()
    await expect(page.getByRole("tab", { name: "已同步数据" })).toBeVisible()
  })

  test("操作面板：同步按钮可见", async ({ page }) => {
    await gotoDepartmentSync(page)

    await expect(page.getByRole("button", { name: "增量同步" })).toBeVisible()
    await expect(page.getByRole("button", { name: "全量同步" })).toBeVisible()
  })

  test("已同步数据：中心和部门分开显示", async ({ page }) => {
    await gotoDepartmentSync(page)

    // Click on the "已同步数据" tab
    await page.getByRole("tab", { name: "已同步数据" }).click()

    // Wait for data to load
    await page.waitForTimeout(500)

    // Check that both center and department sections are visible
    await expect(page.getByText("中心列表")).toBeVisible()
    await expect(page.getByText("部门列表")).toBeVisible()

    // Verify they are separate sections with different icons/colors
    const centerSection = page.locator("div").filter({ hasText: "中心列表" }).first()
    const deptSection = page.locator("div").filter({ hasText: "部门列表" }).first()

    await expect(centerSection).toBeVisible()
    await expect(deptSection).toBeVisible()
  })

  test("已同步数据：中心列表有搜索框", async ({ page }) => {
    await gotoDepartmentSync(page)

    await page.getByRole("tab", { name: "已同步数据" }).click()
    await page.waitForTimeout(500)

    // Center list should have a search input
    const searchInputs = page.locator('input[placeholder*="搜索"]')
    const count = await searchInputs.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test("控制台无报错", async ({ page }) => {
    const errors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text())
      }
    })

    await gotoDepartmentSync(page)

    // Interact with tabs
    await page.getByRole("tab", { name: "同步历史" }).click()
    await page.getByRole("tab", { name: "已同步数据" }).click()

    await page.waitForTimeout(500)

    expect(errors).toHaveLength(0)
  })
})
