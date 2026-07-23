import { expect, test } from "@playwright/test"

test("work report form supports empty detail sections", async ({ page }) => {
  const title = `自动化测试汇报-${Date.now()}`
  await page.goto("/work-reports/new")

  await expect(page.getByTestId("work-report-reporter")).toBeDisabled()
  await expect(page.getByText("工作计划", { exact: true })).toBeVisible()
  await expect(page.getByText("任务总结", { exact: true })).toBeVisible()
  await expect(page.getByText("工作复盘", { exact: true })).toBeVisible()

  await page.getByPlaceholder("例如：研发一部第 31 周工作汇报").fill(title)
  await page.getByRole("button", { name: "提交工作汇报" }).click()

  await expect(page.getByText(/工作汇报(提交|补充)成功/)).toBeVisible()

  await page.goto("/work-reports/mine")
  const reportRow = page.getByRole("row").filter({ hasText: title })
  await expect(reportRow).toBeVisible()
  await reportRow.getByRole("link", { name: "查看详情" }).click()
  await expect(page.getByRole("heading", { name: title })).toBeVisible()
})

test("superuser can open work report field settings", async ({ page }) => {
  await page.goto("/work-reports/config")

  await expect(
    page.getByText("工作汇报字段配置", { exact: true }),
  ).toBeVisible()
  await expect(page.getByRole("checkbox")).toHaveCount(12)
  await expect(page.getByRole("button", { name: "保存配置" })).toBeEnabled()
})

test("superuser can filter all work reports", async ({ page }) => {
  await page.goto("/work-reports/admin")

  await expect(page.getByText("全部工作汇报", { exact: true })).toBeVisible()
  await expect(page.getByPlaceholder("姓名或邮箱")).toBeVisible()
  await expect(page.getByPlaceholder("标题或备注")).toBeVisible()
  await expect(page.getByRole("button", { name: "查询" })).toBeEnabled()
})
