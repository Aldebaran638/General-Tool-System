import { expect, test, type Page } from "@playwright/test"

async function gotoSystemDashboard(page: Page) {
  await page.goto("/system-dashboard")
  await expect(page.getByRole("heading", { name: "系统总览" })).toBeVisible()
}

test.describe("系统总览页面", () => {
  test("页面标题和基本结构可见", async ({ page }) => {
    await gotoSystemDashboard(page)

    await expect(page.getByText("考试系统累计数据统计")).toBeVisible()

    // Summary cards
    await expect(page.getByText("考试场数")).toBeVisible()
    await expect(page.getByText("总参与人次")).toBeVisible()
    await expect(page.getByText("及格率")).toBeVisible()
    await expect(page.getByText("题目总数")).toBeVisible()
    await expect(page.getByText("试卷总数")).toBeVisible()
  })

  test("时间筛选快捷选项可见且可点击", async ({ page }) => {
    await gotoSystemDashboard(page)

    await expect(page.getByText("时间范围")).toBeVisible()

    const shortcuts = ["近7天", "近30天", "近90天", "本年度", "全部"]
    for (const label of shortcuts) {
      const btn = page.getByRole("button", { name: label })
      await expect(btn).toBeVisible()
    }

    // Click "近7天" and verify it becomes active (default variant)
    await page.getByRole("button", { name: "近7天" }).click()
    const activeBtn = page.getByRole("button", { name: "近7天" })
    // The Button component with variant="default" gets bg-primary class
    await expect(activeBtn).toHaveClass(/bg-primary/)
  })

  test("自定义日期筛选可展开", async ({ page }) => {
    await gotoSystemDashboard(page)

    await page.getByRole("button", { name: "自定义" }).click()

    // Date inputs should appear — locate by the visible label text above them
    await expect(page.getByText("开始日期", { exact: true })).toBeVisible()
    await expect(page.getByText("结束日期", { exact: true })).toBeVisible()
  })

  test("图表区域显示设备终端分布和题型分布", async ({ page }) => {
    await gotoSystemDashboard(page)

    await expect(page.getByText("考试终端分布")).toBeVisible()
    await expect(page.getByText("题库题型分布")).toBeVisible()

    // Difficulty chart should NOT be present
    await expect(page.getByText("题库难易度占比")).not.toBeVisible()
  })

  test("切换时间筛选后图表数据应更新（网络请求验证）", async ({ page }) => {
    await gotoSystemDashboard(page)

    // Click last7 and wait for new request with query params
    const [response] = await Promise.all([
      page.waitForResponse(
        (resp) =>
          resp.url().includes("/api/v1/exams/admin/dashboard/stats") &&
          resp.url().includes("start_date="),
        { timeout: 10000 },
      ),
      page.getByRole("button", { name: "近7天" }).click(),
    ])

    expect(response.status()).toBe(200)
  })

  test("控制台无报错", async ({ page }) => {
    const errors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text())
      }
    })

    await gotoSystemDashboard(page)

    // Interact with filters
    await page.getByRole("button", { name: "近30天" }).click()
    await page.getByRole("button", { name: "自定义" }).click()

    // Wait a bit for any async rendering
    await page.waitForTimeout(500)

    expect(errors).toHaveLength(0)
  })
})
