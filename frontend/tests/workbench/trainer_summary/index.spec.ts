import { expect, test, type Page } from "@playwright/test"

async function gotoTrainerSummary(page: Page) {
  await page.goto("/trainer-summary")
  await expect(page.getByRole("heading", { name: "培训讲师汇总" })).toBeVisible()
}

test.describe("培训讲师汇总页面", () => {
  test("页面标题和基本结构可见", async ({ page }) => {
    await gotoTrainerSummary(page)

    // Subtitle shows trainer count
    await expect(page.getByText(/共 \d+ 位讲师/)).toBeVisible()

    // Search input
    await expect(
      page.getByPlaceholder("搜索讲师姓名或课程名称..."),
    ).toBeVisible()

    // Date filter
    await expect(page.getByText("时间范围")).toBeVisible()
  })

  test("搜索框可输入并触发搜索", async ({ page }) => {
    await gotoTrainerSummary(page)

    const searchInput = page.getByPlaceholder("搜索讲师姓名或课程名称...")
    await searchInput.fill("测试讲师")

    // Wait for debounced search request
    await page.waitForResponse((resp) =>
      resp.url().includes("/api/v1/exams/admin/trainers/summary"),
    )
  })

  test("时间筛选快捷选项可用", async ({ page }) => {
    await gotoTrainerSummary(page)

    const shortcuts = ["近7天", "近30天", "近90天", "本年度", "全部"]
    for (const label of shortcuts) {
      await expect(page.getByRole("button", { name: label })).toBeVisible()
    }

    await page.getByRole("button", { name: "近30天" }).click()

    // Should trigger a request with date params
    await page.waitForResponse((resp) =>
      resp.url().includes("/api/v1/exams/admin/trainers/summary"),
    )
  })

  test("自定义日期筛选可展开", async ({ page }) => {
    await gotoTrainerSummary(page)

    await page.getByRole("button", { name: "自定义" }).click()
    await expect(page.getByText("开始日期", { exact: true })).toBeVisible()
    await expect(page.getByText("结束日期", { exact: true })).toBeVisible()
  })

  test("按讲师分组展示：每个讲师卡片包含姓名、授课次数、培训人数", async ({ page }) => {
    await gotoTrainerSummary(page)

    // Wait for the trainer cards to render (data already loaded from previous tests)
    await expect(page.getByText(/共 \d+ 位讲师/)).toBeVisible()

    // Check if trainer cards are present (if there's data)
    const cards = page.locator("[class*='card']").filter({ hasText: "授课" })
    const count = await cards.count()

    if (count > 0) {
      // Verify card structure
      const firstCard = cards.first()
      await expect(firstCard.locator("text=/授课 \\d+ 次/")).toBeVisible()
      await expect(firstCard.locator("text=/培训 \\d+ 人/")).toBeVisible()
    }
  })

  test("课程名称可点击跳转考试详情", async ({ page }) => {
    await gotoTrainerSummary(page)

    // Wait for data to be visible
    await expect(page.getByText(/共 \d+ 位讲师/)).toBeVisible()

    // Look for exam name links
    const examLink = page.locator("a[href*='/exams/']").first()
    if (await examLink.isVisible().catch(() => false)) {
      await examLink.click()
      await expect(page).toHaveURL(/\/exams\//)
    }
  })

  test("控制台无报错", async ({ page }) => {
    const errors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text())
      }
    })

    await gotoTrainerSummary(page)

    // Interact with filters
    await page.getByPlaceholder("搜索讲师姓名或课程名称...").fill("测试")
    await page.getByRole("button", { name: "近7天" }).click()
    await page.getByRole("button", { name: "自定义" }).click()

    await page.waitForTimeout(500)

    expect(errors).toHaveLength(0)
  })
})
