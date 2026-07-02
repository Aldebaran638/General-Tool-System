import { expect, test, type Page } from "@playwright/test"

async function gotoExamList(page: Page) {
  await page.goto("/exams")
  await expect(page.getByRole("heading", { name: "考试管理" })).toBeVisible()
}

test.describe("考试详情页 - 参与者管理", () => {
  test("考试列表页可打开", async ({ page }) => {
    await gotoExamList(page)
    await expect(page.getByRole("button", { name: "新建考试" })).toBeVisible()
  })

  test("点击考试进入详情页，参与者标签可见", async ({ page }) => {
    await gotoExamList(page)

    // Wait for exam list to load
    await page.waitForTimeout(500)

    // Click on first exam row to enter detail page
    const firstExamLink = page.locator("table tbody tr td a").first()
    if (await firstExamLink.isVisible().catch(() => false)) {
      await firstExamLink.click()
      await page.waitForURL(/\/exams\//, { timeout: 5000 })

      // Check that participants tab exists
      await expect(page.getByRole("tab", { name: "参与者" })).toBeVisible()
    }
  })

  test("参与者标签页：添加学员区域可见", async ({ page }) => {
    await gotoExamList(page)
    await page.waitForTimeout(500)

    // Find a DRAFT exam (only draft exams can add participants)
    const examLinks = page.locator("table tbody tr")
    const count = await examLinks.count()

    let foundDraft = false
    for (let i = 0; i < count; i++) {
      const row = examLinks.nth(i)
      const statusCell = row.locator("td").nth(2) // Status column
      const statusText = await statusCell.textContent()

      if (statusText?.includes("未发布")) {
        // Click on exam name to open detail
        const nameLink = row.locator("td a").first()
        await nameLink.click()
        foundDraft = true
        break
      }
    }

    if (!foundDraft) {
      test.skip()
      return
    }

    // Wait for detail page
    await page.waitForURL(/\/exams\//, { timeout: 5000 })

    // Click participants tab
    await page.getByRole("tab", { name: "参与者" }).click()

    // Check add participant section
    await expect(page.getByText("添加学员")).toBeVisible()
    await expect(page.getByRole("button", { name: "按中心" })).toBeVisible()
    await expect(page.getByRole("button", { name: "按部门" })).toBeVisible()
    await expect(page.getByRole("button", { name: "按人员" })).toBeVisible()
  })

  test("按中心添加：多选功能可用", async ({ page }) => {
    await gotoExamList(page)
    await page.waitForTimeout(500)

    // Find a DRAFT exam
    const examLinks = page.locator("table tbody tr")
    const count = await examLinks.count()

    let foundDraft2 = false
    for (let i = 0; i < count; i++) {
      const row = examLinks.nth(i)
      const statusCell = row.locator("td").nth(2)
      const statusText = await statusCell.textContent()

      if (statusText?.includes("未发布")) {
        const nameLink = row.locator("td a").first()
        await nameLink.click()
        foundDraft2 = true
        break
      }
    }

    if (!foundDraft2) {
      test.skip()
      return
    }

    await page.waitForURL(/\/exams\//, { timeout: 5000 })
    await page.getByRole("tab", { name: "参与者" }).click()

    // Click "按中心" button
    await page.getByRole("button", { name: "按中心" }).click()

    // Check that search box and checkbox list appear
    await expect(page.getByPlaceholder("搜索中心名称...")).toBeVisible()

    // The checkbox list should be visible (even if empty)
    const checkboxList = page.locator("div.rounded-md.border.bg-card")
    await expect(checkboxList.first()).toBeVisible()
  })

  test("按部门添加：多选功能可用", async ({ page }) => {
    await gotoExamList(page)
    await page.waitForTimeout(500)

    // Find a DRAFT exam
    const examLinks = page.locator("table tbody tr")
    const count = await examLinks.count()

    let foundDraft3 = false
    for (let i = 0; i < count; i++) {
      const row = examLinks.nth(i)
      const statusCell = row.locator("td").nth(2)
      const statusText = await statusCell.textContent()

      if (statusText?.includes("未发布")) {
        const nameLink = row.locator("td a").first()
        await nameLink.click()
        foundDraft3 = true
        break
      }
    }

    if (!foundDraft3) {
      test.skip()
      return
    }

    await page.waitForURL(/\/exams\//, { timeout: 5000 })
    await page.getByRole("tab", { name: "参与者" }).click()

    // Click "按部门" button
    await page.getByRole("button", { name: "按部门" }).click()

    // Check that search box and checkbox list appear
    await expect(page.getByPlaceholder("搜索部门名称...")).toBeVisible()

    const checkboxList = page.locator("div.rounded-md.border.bg-card")
    await expect(checkboxList.first()).toBeVisible()
  })

  test("控制台无报错", async ({ page }) => {
    const errors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text())
      }
    })

    await gotoExamList(page)
    await page.waitForTimeout(500)

    // Try to interact with exam list
    const firstLink = page.locator("table tbody tr td a").first()
    if (await firstLink.isVisible().catch(() => false)) {
      await firstLink.click()
      await page.waitForURL(/\/exams\//, { timeout: 5000 })

      await page.getByRole("tab", { name: "参与者" }).click()
      await page.getByRole("button", { name: "按中心" }).click()
      await page.getByRole("button", { name: "按部门" }).click()
      await page.getByRole("button", { name: "按人员" }).click()
    }

    await page.waitForTimeout(500)
    expect(errors).toHaveLength(0)
  })
})
