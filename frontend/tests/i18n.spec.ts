import { expect, test, type Page } from "@playwright/test"

test.describe("国际化 (i18n)", () => {
  test.use({ locale: "zh-CN" })

  test.beforeEach(async ({ page }) => {
    // 依赖 chromium project 的 storageState 提供登录态。
    // 进入 settings 后清空 app_locale，再 reload 让 I18nProvider 走默认推断路径。
    await page.goto("/settings")
    await page.evaluate(() => localStorage.removeItem("app_locale"))
    await page.reload()
    await expect(page.locator("#language-select")).toBeVisible()
  })

  async function selectLocale(page: Page, optionName: RegExp) {
    await page.locator("#language-select").click()
    await page.getByRole("option", { name: optionName }).click()
  }

  test("设置页面语言选择器可见", async ({ page }) => {
    await expect(page.locator("#language-select")).toBeVisible()
  })

  test("默认语言写入 localStorage 为 zh-CN", async ({ page }) => {
    await expect
      .poll(async () =>
        page.evaluate(() => localStorage.getItem("app_locale")),
      )
      .toBe("zh-CN")
  })

  test("切换为英文后 localStorage 与 UI 同步刷新", async ({ page }) => {
    await selectLocale(page, /English/)
    await expect
      .poll(async () =>
        page.evaluate(() => localStorage.getItem("app_locale")),
      )
      .toBe("en-US")
    await expect(
      page.getByRole("heading", { name: "Settings" }),
    ).toBeVisible()
  })

  test("切换为繁体中文后 UI 文案同步刷新", async ({ page }) => {
    await selectLocale(page, /繁體中文/)
    await expect
      .poll(async () =>
        page.evaluate(() => localStorage.getItem("app_locale")),
      )
      .toBe("zh-TW")
    await expect(
      page.getByRole("heading", { name: "設定" }),
    ).toBeVisible()
  })

  test("刷新后语言偏好持久化", async ({ page }) => {
    await selectLocale(page, /English/)
    await expect
      .poll(async () =>
        page.evaluate(() => localStorage.getItem("app_locale")),
      )
      .toBe("en-US")
    await page.reload()
    const locale = await page.evaluate(() =>
      localStorage.getItem("app_locale"),
    )
    expect(locale).toBe("en-US")
    await expect(
      page.getByRole("heading", { name: "Settings" }),
    ).toBeVisible()
  })

  test("切换为英文后导航文案与子项同步变化", async ({ page }) => {
    await selectLocale(page, /English/)
    const nav = page.locator("nav")
    await expect(nav.getByText("Finance", { exact: true })).toBeVisible()
    await expect(
      nav.getByText("Purchase Records", { exact: true }),
    ).toBeVisible()
    await expect(
      nav.getByText("Invoice Files", { exact: true }),
    ).toBeVisible()
  })

  test("切换为繁体中文后导航子项显示繁体", async ({ page }) => {
    await selectLocale(page, /繁體中文/)
    const nav = page.locator("nav")
    await expect(nav.getByText("財務", { exact: true })).toBeVisible()
    await expect(nav.getByText("購買記錄", { exact: true })).toBeVisible()
    await expect(nav.getByText("發票檔案", { exact: true })).toBeVisible()
  })
})
