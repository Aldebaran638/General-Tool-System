# Round 003 Frontend Report - frontend_i18n

> 本报告覆盖 Round 003 初次实现 + 后续修复（FE-I18N-FIX-001 ~ FE-I18N-FIX-006）。
> 修复依据为 `docs/rounds/round-003/tasks.md`、`docs/rounds/round-003/test-plan.md` 及验收反馈。

## 输入物路径

- `skills/members/前端skill.md`
- `skills/tool-system/system-principles.md`
- `skills/tool-system/group-tool-contract.md`
- `docs/rounds/round-003/requirements.md`
- `docs/rounds/round-003/design.md`
- `docs/rounds/round-003/test-plan.md`
- `docs/rounds/round-003/tasks.md`
- `frontend/src/i18n/`（dictionaries/, I18nProvider.tsx, locales.ts, types.ts, index.ts）
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/routes/_layout.tsx`
- `frontend/src/routes/_layout/settings.tsx`
- `frontend/src/routes/_layout/admin.tsx`
- `frontend/src/components/Sidebar/AppSidebar.tsx`
- `frontend/src/components/Sidebar/User.tsx`
- `frontend/src/components/UserSettings/LanguageSelector.tsx`
- `frontend/src/tools/registry.ts`
- `frontend/src/tools/finance/purchase_records/index.ts`
- `frontend/src/tools/finance/invoice_files/index.ts`
- `frontend/tests/i18n.spec.ts`

## 本轮修复（FE-I18N-FIX-001 ~ 006）

### FE-I18N-FIX-001 工具导航子项真正多语言

修改：

- `frontend/src/tools/registry.ts`
  - `ToolRouteConfig` 与 `ToolNavigationConfig` 新增可选 `titleKey?: string`。
  - `getNavigationEntries(context, t)` 在生成子项时优先使用 `tool.navigation.titleKey` 走 `t()` 翻译，缺省回退原 `tool.navigation.title`。
  - 工具组名称仍通过 `_formatGroupName` → `t("finance.groupName")` 翻译。
- `frontend/src/tools/finance/purchase_records/index.ts`
  - `navigation.titleKey = "finance.purchaseRecords.title"`，`title` 保留作为字典缺失时的回退。
- `frontend/src/tools/finance/invoice_files/index.ts`
  - `navigation.titleKey = "finance.invoiceFiles.title"`，`title` 保留作为回退。

字典命中：

| Locale | `finance.groupName` | `finance.purchaseRecords.title` | `finance.invoiceFiles.title` |
|--------|---------------------|---------------------------------|------------------------------|
| zh-CN  | 财务                | 购买记录                        | 发票文件                     |
| en-US  | Finance             | Purchase Records                | Invoice Files                |
| zh-TW  | 財務                | 購買記錄                        | 發票檔案                     |

工具自注册结构未变，仅在 navigation 中追加可选 `titleKey`。

### FE-I18N-FIX-002 修复 Playwright 对 shadcn Select 的错误用法

修改：`frontend/tests/i18n.spec.ts` 完整重写。

- 移除所有 `locator("#language-select").selectOption(...)`（shadcn Select 不是原生 `<select>`，此调用必然失败）。
- 改为真实交互：
  - `await page.locator("#language-select").click()` 打开 Radix Portal 下拉。
  - `await page.getByRole("option", { name: /English/ }).click()` 通过 Radix `[role="option"]` 与 accessible name 匹配。
- 抽出 `selectLocale(page, optionName: RegExp)` 辅助函数，三种语言通过正则匹配 LOCALE_LABELS（`简体中文` / `English` / `繁體中文`）。
- 不依赖 `selectOption()`，无需为 trigger/option 添加额外 `data-testid`，复用既有 `id="language-select"`。

### FE-I18N-FIX-003 默认语言持久化（方案 A）

修改：`frontend/src/i18n/I18nProvider.tsx`

- `getInitialLocale()` 在没有 `getStoredLocale()` 命中时，会立即调用 `storeLocale(detected)` 把推断出的 locale 写入 `localStorage.app_locale`。
- 行为：
  - 已有 stored locale → 直接使用（保持原有刷新保持逻辑）。
  - 无 stored locale → 走 `detectBrowserLocale()`（按 `navigator.language`），落地到 `app_locale`。

**选择理由**：
- 与设计文档「localStorage key：`app_locale`，默认 `zh-CN`，按浏览器语言推断」一致，将默认值显式持久化能让刷新行为更稳定，并且让外部观察者（Playwright、调试工具）始终看到 UI 实际使用的语言。
- 方案 B 会留下「UI 已经用 zh-CN 但 localStorage 是空」的不一致状态，对后续接入用户偏好、跨标签同步等都更易踩坑。
- StrictMode 下 `useState` 初始化函数可能调用两次，但 `storeLocale` 是幂等写入，无副作用。

### FE-I18N-FIX-004 清理垃圾/临时文件

已删除：

- `console.error('ERR'`（仓库根，bash 重定向出错产物）
- `console.error(e.message))`（仓库根，bash 重定向出错产物）
- `frontend/src/test_brace.ts`（测试用空 export，仓库不需要）
- `test_utf8.txt`（仓库根，UTF-8 调试残留）

确认不存在（无需操作）：

- `scripts/fix_build.py`
- `scripts/fix_schemas.py`
- `frontend/tests/i18n.spec.ts.tmp`

未删除业务文件、未删除文档、未触碰后端/skill/无关工具。

### FE-I18N-FIX-005 更新 frontend-report

即本文档。重新核对了上一版报告中的"无垃圾文件残留"声明，本轮已实际删除残留并复核。

### FE-I18N-FIX-006 Sidebar User 菜单 i18n

修改：`frontend/src/components/Sidebar/User.tsx`

- 新增 `import { useI18n } from "@/i18n"`，在 `User` 组件内取出 `const { t } = useI18n()`。
- "User Settings"（菜单项 fallback 文案）替换为 `t("navigation.userSettingsMenu")`，保留原 `user?.full_name || ...` 的回退语义，仅把硬编码英文换成翻译值。
- "Log Out" 替换为 `t("navigation.logout")`。

复用既有字典键，**未新增任何 key**，因为 dictionary 中已有完全匹配任务包要求的字段：

| Key | zh-CN | en-US | zh-TW |
|-----|-------|-------|-------|
| `navigation.userSettingsMenu` | 用户设置 | User Settings | 使用者設定 |
| `navigation.logout` | 退出登录 | Log Out | 登出 |

未改动 DropdownMenu 行为：`handleLogout` / `handleMenuClick` 逻辑、菜单结构、`SidebarMenuButton` / `UserInfo` / `Avatar` / `ChevronsUpDown` 节点、样式 className 均未变，仅替换两个文本节点。

## 修改文件汇总

| 路径 | 类型 |
|------|------|
| `frontend/src/tools/registry.ts` | 修改 |
| `frontend/src/tools/finance/purchase_records/index.ts` | 修改 |
| `frontend/src/tools/finance/invoice_files/index.ts` | 修改 |
| `frontend/src/i18n/I18nProvider.tsx` | 修改 |
| `frontend/src/components/Sidebar/User.tsx` | 修改 |
| `frontend/tests/i18n.spec.ts` | 重写 |
| `docs/rounds/round-003/frontend-report.md` | 重写 |
| `console.error('ERR'` | 删除 |
| `console.error(e.message))` | 删除 |
| `frontend/src/test_brace.ts` | 删除 |
| `test_utf8.txt` | 删除 |

新增文件：本轮修复无新增文件（i18n 基础设施在初始实现轮已建立）。

## 路由 / 工具组注册

- 路由：未新增、未删除。`/finance/purchase-records` 与 `/finance/invoice-files` 路由保持原状。
- 工具组：保留 `finance` 工具组；本轮仅让两个工具的 sidebar 标题真正走 i18n。

## 调用了哪些 API

本轮修复未新增任何 API 调用，未修改请求 URL、payload 或 header。

## 新增或修改了哪些测试

- 重写 `frontend/tests/i18n.spec.ts`，覆盖：
  - `设置页面语言选择器可见`
  - `默认语言写入 localStorage 为 zh-CN`（依赖 FE-I18N-FIX-003 的 Provider 改动）
  - `切换为英文后 localStorage 与 UI 同步刷新`（验证 settings heading 切到 "Settings"）
  - `切换为繁体中文后 UI 文案同步刷新`（验证 settings heading 切到 "設定"）
  - `刷新后语言偏好持久化`
  - `切换为英文后导航文案与子项同步变化`（验证 sidebar `Finance` / `Purchase Records` / `Invoice Files`，依赖 FE-I18N-FIX-001）
  - `切换为繁体中文后导航子项显示繁体`（验证 sidebar `財務` / `購買記錄` / `發票檔案`）
- `test.use({ locale: "zh-CN" })` 锁定浏览器语言，让 `detectBrowserLocale()` 在容器中得到稳定结果。
- `beforeEach` 清空 `localStorage.app_locale` + reload，确保从默认推断路径开始。

## 校验命令与真实结果

### 1. 前端构建

```bash
docker compose exec -T frontend bun run build
```

结果：**通过**（exit 0，4.89s ~ 5.08s）。完整真实输出：

```
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
transforming...
✓ 2237 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                     0.57 kB │ gzip:   0.34 kB
dist/assets/index-CSbaHi74.css                     67.94 kB │ gzip:  11.86 kB
dist/assets/finance.invoice-files-Cb640E6p.js       0.17 kB │ gzip:   0.16 kB
dist/assets/finance.purchase-records-P6gWMClS.js    0.17 kB │ gzip:   0.16 kB
dist/assets/items-BeKYtRiu.js                       0.17 kB │ gzip:   0.16 kB
dist/assets/index-Cw4BGDWV.js                       0.36 kB │ gzip:   0.27 kB
dist/assets/recover-password-BUCscAWC.js            1.35 kB │ gzip:   0.70 kB
dist/assets/reset-password-ILpcgZwE.js              2.01 kB │ gzip:   0.88 kB
dist/assets/login-bMe9Do1I.js                       3.22 kB │ gzip:   1.46 kB
dist/assets/settings-CEyvMPOC.js                    7.09 kB │ gzip:   2.34 kB
dist/assets/admin-pvYcFTkC.js                      17.76 kB │ gzip:   5.30 kB
dist/assets/index-DYj2iygS.js                     843.85 kB │ gzip: 251.35 kB
✓ built in 5.08s
```

> chunk size 警告与本轮无关（既存代码切分问题）。TypeScript 编译 + vite 构建均无错误。

> 追加 FIX-006（User.tsx i18n）后再次执行 `docker compose exec -T frontend bun run build`，4.76s 完成构建（exit 0），无 TypeScript / Vite 错误，bundle 切分与上方输出一致。

### 2. Playwright 测试

任务包指定命令：

```bash
docker compose exec -T frontend bun run test -- tests/i18n.spec.ts --reporter=line --timeout=15000
```

实际执行结果：**未能执行用例，被外层超时杀死**。

| 字段 | 值 |
|------|-----|
| 真实命令 | `docker compose exec -T frontend bun run test -- tests/i18n.spec.ts --reporter=line --timeout=15000` |
| 外层 timeout 设置 | 60s |
| 真实退出码 | 124（外层 `timeout` 强杀） |
| 用例级 timeout | 15s（命令参数，但未进入用例执行阶段） |
| 真实输出 | `$ bun x playwright test "tests/i18n.spec.ts" "--reporter=line" "--timeout=15000"` 之后零输出 |

### 3. Playwright 阻塞根因再次诊断

诊断命令（在前端容器内）：

```bash
ldd /root/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome | grep "not found" | head -20
```

输出（截取，仍报告大量缺失）：

```
libglib-2.0.so.0 => not found
libgobject-2.0.so.0 => not found
libnspr4.so => not found
libnss3.so => not found
libnssutil3.so => not found
libsmime3.so => not found
libdbus-1.so.3 => not found
libgio-2.0.so.0 => not found
libatk-1.0.so.0 => not found
libatk-bridge-2.0.so.0 => not found
libcups.so.2 => not found
libexpat.so.1 => not found
libxcb.so.1 => not found
libxkbcommon.so.0 => not found
libatspi.so.0 => not found
libX11.so.6 => not found
libXcomposite.so.1 => not found
libXdamage.so.1 => not found
libXext.so.6 => not found
libXfixes.so.3 => not found
```

附加观察：

- `/root/.cache/ms-playwright/chromium-1200/` 下存在 `DEPENDENCIES_VALIDATED` 标记，但实际 `ldd` 仍报缺失，说明该标记是镜像构建时一次性写入，与运行时实际系统包不同步。
- 容器内 Playwright 1.57.0 已安装，浏览器二进制已下载，但启动时因 dynamic linker 找不到这些库而进程挂起，无任何 stderr 输出（与上一轮完全同源）。

**结论**：Playwright 仍因前端容器缺系统包（`libglib2.0-0`, `libnss3`, `libx11-6`, `libxcomposite1`, `libxdamage1`, `libxext6`, `libxfixes3`, `libxrandr2`, `libgbm1`, `libpango-1.0-0`, `libcups2`, `libxkbcommon0`, `libatspi2.0-0`, `libasound2` 等共 20+ 个）无法运行。该问题需要在 `frontend/Dockerfile` 中通过 `apt-get install` 或 `bunx playwright install --with-deps chromium` 处理，超出本轮前端代码修复范围（属于环境/容器编排，已在 INT/Round 005 之前的前端报告中持续标记）。

## 越界自检

| 检查项 | 结论 |
|--------|------|
| 是否仅修改任务包 `允许修改` 范围内文件 | ✅ 是 |
| 是否动了 `backend/**` | ❌ 没有 |
| 是否动了 `skills/**` | ❌ 没有 |
| 是否动了 Round 005 / Round 008 文件 | ❌ 没有 |
| 是否动了与 i18n 无关的业务逻辑 | ❌ 没有，registry/index.ts 改动只新增 `titleKey` 字段，未改变业务行为 |
| 是否修改 API payload code | ❌ 没有，`titleKey` 只影响前端展示 |
| 是否破坏现有工具自注册 | ❌ 没有，结构兼容（`titleKey` 为可选字段） |
| 是否擅自迁移 i18n.spec.ts 目录结构 | ❌ 没有，按任务包 `允许修改` 列表保留在 `frontend/tests/i18n.spec.ts` |
| 是否引入新视觉语言 | ❌ 没有，UI 未变 |
| 是否仍有垃圾文件残留 | ❌ 已逐文件 `ls` 验证不存在（详见 FE-I18N-FIX-004） |
| 是否手动修改 `routeTree.gen.ts` | ❌ 没有 |

## 联调检查（前端已验证项 / 未验证项）

### 已验证

- TypeScript 严格构建通过（`tsc -p tsconfig.build.json` 无报错），`titleKey` 类型变更不破坏既有 `ToolModuleConfig` 使用方。
- Vite 生产构建通过，bundle 切分正常。
- 字典 key `finance.groupName`、`finance.purchaseRecords.title`、`finance.invoiceFiles.title` 在三种语言字典中均已落地（人工核对 `dictionaries/{zh-CN,en-US,zh-TW}/index.ts` 与 `finance.ts`）。
- `I18nProvider` 默认写入逻辑代码层正确：无 stored locale → `detectBrowserLocale` → `storeLocale`。
- shadcn Select Radix 实现确认：`SelectItem` 渲染 `[role="option"]`，accessible name 来自 `SelectPrimitive.ItemText`，与新测试匹配方式一致。

### 未验证（受 Playwright 环境阻塞）

- 浏览器实际渲染下：sidebar 切换语言后子项立刻显示翻译值。
- 浏览器实际渲染下：`localStorage.app_locale` 在首次访问时被自动写入。
- 真正运行 `i18n.spec.ts` 7 个用例的通过情况。
- `playwright/.auth/user.json` storage state 复用情况。

## 未完成项

- ❌ `i18n.spec.ts` 真实跑通：因前端容器缺 Chromium 系统库（`libglib-2.0.so.0`, `libnss3.so`, `libX11.so.6` 等 20+ 项），Playwright 启动后挂起、零输出，60s 外层 timeout 强杀（exit 124）。本轮前端代码修复范围内无法解决，**需要在 `frontend/Dockerfile` 安装系统依赖（`apt-get install` 一组运行库或 `bunx playwright install-deps`）后重跑**。
- ❌ `playwright/.auth/user.json`（auth.setup.ts 产物）同样受上面 Chromium 启动阻塞影响，未生成。
