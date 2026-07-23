import { expect, test } from "@playwright/test"

test("work report form supports empty detail sections", async ({ page }) => {
  await page.goto("/work-reports/new")

  await expect(page.getByTestId("work-report-reporter")).toBeDisabled()
  await expect(page.getByText("工作计划", { exact: true })).toBeVisible()
  await expect(page.getByText("任务总结", { exact: true })).toBeVisible()
  await expect(page.getByText("工作复盘", { exact: true })).toBeVisible()

  await page
    .getByPlaceholder("例如：研发一部第 31 周工作汇报")
    .fill(`自动化测试汇报-${Date.now()}`)
  await page.getByRole("button", { name: "提交工作汇报" }).click()

  await expect(page.getByText(/工作汇报(提交|补充)成功/)).toBeVisible()
})

test("superuser can open work report field settings", async ({ page }) => {
  await page.goto("/work-reports/config")

  await expect(
    page.getByText("工作汇报字段配置", { exact: true }),
  ).toBeVisible()
  await expect(page.getByRole("checkbox")).toHaveCount(12)
  await expect(page.getByRole("button", { name: "保存配置" })).toBeEnabled()
})
