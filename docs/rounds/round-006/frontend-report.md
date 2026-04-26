# Round 006 Frontend Report - remove_workbench_project_management

> 本报告对应 Round 006 前端任务派单（`docs/rounds/round-006/dispatch-frontend.md`），覆盖 workbench 示例工具的前端代码删除。

## 输入物路径

- `skills/members/架构师skill.md`
- `skills/members/前端skill.md`
- `docs/rounds/round-006/requirements.md`
- `docs/rounds/round-006/design.md`
- `docs/rounds/round-006/test-plan.md`
- `docs/rounds/round-006/tasks.md`
- `docs/rounds/round-006/dispatch-frontend.md`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/tools/registry.ts`
- `frontend/src/tools/workbench/project_management/`（删除前 6 个源文件）
- `frontend/src/routes/_layout/items.tsx`（删除前）
- `frontend/src/components/Items/`（删除前 5 个文件）
- `frontend/src/components/Pending/PendingItems.tsx`（已读，未删）
- `frontend/tests/items/index.spec.ts`（删除前）
- `frontend/tests/workbench/project_management/index.spec.ts`（删除前）
- `frontend/src/i18n/dictionaries/en-US/admin.ts`（已读，未改）
- `frontend/src/routeTree.gen.ts`（构建自动重写）

## 范围说明

任务包标题为 `remove_workbench`，`允许修改` 仅显式列出 workbench 自身的目录与 `tool-navigation.tsx`，但 workbench 工具的渲染层文件通过硬编码 import 直接依赖 `@/tools/workbench/project_management/...`：

- `src/components/Items/AddItem.tsx`、`columns.tsx`、`DeleteItem.tsx`、`EditItem.tsx` 都 `import { ... } from "@/tools/workbench/project_management/api|schemas|types"`。
- `src/components/Items/ItemActionsMenu.tsx` 引用 `./DeleteItem`、`./EditItem`，与上面四文件构成内部环。
- `src/routes/_layout/items.tsx` 通过 `toolRegistry.getTool("project_management")` 取页面，工具组件来自 workbench 模块；删除 workbench 目录后该路由不再有效。

任务包同时要求 `bun run build` 通过、`不应再出现前端 workbench 工具 import、路由、测试引用`，且禁止手动修改 `frontend/src/routeTree.gen.ts`。Round 006 设计文档 `design.md` `### 工具删除` / `### 文案清理` 已显式将 `items.tsx`、`components/Items/`、`tests/items/` 列入删除范围。

经与用户确认，本轮按"扩展到依赖项"路径执行：除任务包列出的 workbench 自身文件外，同步删除上述会因 workbench 删除而 TS 编译失败的依赖文件，使 `bun run build` 保持通过。所有删除均与 workbench/project_management 强耦合，不涉及 finance 或平台基础页面。

## 删除文件 / 目录

### 任务包显式列出

| 路径 | 说明 |
|------|------|
| `frontend/src/tools/workbench/project_management/api.ts` | 工具 API |
| `frontend/src/tools/workbench/project_management/components/ProjectManagementPage.tsx` | 工具页面组件 |
| `frontend/src/tools/workbench/project_management/hooks/useItemsQuery.ts` | React Query hook |
| `frontend/src/tools/workbench/project_management/schemas.ts` | 表单 schema |
| `frontend/src/tools/workbench/project_management/types.ts` | 类型定义 |
| `frontend/src/tools/workbench/project_management/index.ts` | 自注册入口 |
| `frontend/src/tools/workbench/project_management/`（目录） | project_management 工具目录 |
| `frontend/src/tools/workbench/`（目录） | 删除 project_management 后空目录 |
| `frontend/tests/workbench/project_management/index.spec.ts` | workbench 路径下的项目管理 Playwright |
| `frontend/tests/workbench/project_management/`（目录） | 删除测试文件后空目录 |
| `frontend/tests/workbench/`（目录） | 删除 project_management 后空目录 |

注：任务包列出的 `frontend/src/routes/_layout/workbench.project-management.tsx` 在仓库中不存在；实际项目管理路由是下表的 `frontend/src/routes/_layout/items.tsx`。

### 因 workbench 删除而必须同步删除（用户确认）

| 路径 | 删除原因 |
|------|----------|
| `frontend/src/routes/_layout/items.tsx` | 通过 `toolRegistry.getTool("project_management")` 取组件；workbench 删除后该路由没有可用页面，且设计文档 `### 工具删除` 已列出。 |
| `frontend/src/components/Items/AddItem.tsx` | `import { createItem, itemsQueryKey } from "@/tools/workbench/project_management/api"` 等 — 删除 workbench 后 TS 解析失败。 |
| `frontend/src/components/Items/columns.tsx` | `import type { ItemPublic } from "@/tools/workbench/project_management/types"` |
| `frontend/src/components/Items/DeleteItem.tsx` | `import { ... } from "@/tools/workbench/project_management/api"` |
| `frontend/src/components/Items/EditItem.tsx` | `import { ... } from "@/tools/workbench/project_management/api\|schemas\|types"` |
| `frontend/src/components/Items/ItemActionsMenu.tsx` | `import DeleteItem from "../Items/DeleteItem"`、`import EditItem from "../Items/EditItem"` — 兄弟文件全删。 |
| `frontend/src/components/Items/`（目录） | 上述五文件清空后空目录。 |
| `frontend/tests/items/index.spec.ts` | 用例点击 `项目管理` 链接、断言 `/items` 路由 — 两者均已不存在。 |
| `frontend/tests/items/`（目录） | 删除测试文件后空目录。 |

### 没有删除的相关文件（说明）

| 路径 | 处理 | 原因 |
|------|------|------|
| `frontend/src/components/Pending/PendingItems.tsx` | 保留 | 仅被被删的 `ProjectManagementPage` 引用，已成孤儿；任务包 `允许修改` 不含 `Pending/`；不影响构建，列入"未完成项"。 |
| `frontend/tests/utils/random.ts` 中 `randomItemTitle` / `randomItemDescription` | 保留 | 仅被被删的 items / workbench 测试引用；导出未被使用不会破坏构建，留作历史。 |
| `frontend/src/i18n/dictionaries/en-US/admin.ts` 中 `"All items associated with this user will be permanently deleted..."` | 保留 | 任务包写明 `frontend/src/i18n/**，除非删除 workbench 后构建必须修复引用` — 该文案不影响构建，按规则不动；列入"未完成项"。设计文档 `### 文案清理` 仍建议中性化。 |
| `frontend/src/tools/registry.ts:35` 注释 `e.g., "workbench"` | 保留 | 是 `ToolModuleConfig.group` 的 JSDoc 示例，非真实引用；`registry.ts` 不在 `允许修改` 列表；按任务包"如果只剩文档或历史说明，可以在报告中说明"处理。 |

## 修改文件

| 路径 | 修改内容 |
|------|----------|
| `frontend/src/config/tool-navigation.tsx` | 删除第 13 行 `import "@/tools/workbench/project_management"`；其余 finance import、平台 navigation builder 不动。 |

构建过程自动重写：

| 路径 | 自动改动 |
|------|----------|
| `frontend/src/routeTree.gen.ts` | TanStack Router codegen 在 `tsc -p tsconfig.build.json && vite build` 链路中刷新；不再 import `LayoutItemsRouteImport`、不再声明 `/items` / `/_layout/items` / `LayoutItemsRoute`。**未手动编辑**。 |

## 路由 / 工具组注册

- 路由：删除 `/_layout/items`；其余路由保持原状（`__root__` / `/_layout` / `/_layout/admin` / `/_layout/settings` / `/_layout/` / `/_layout/finance/invoice-files` / `/_layout/finance/purchase-records` / `/login` / `/signup` / `/recover-password` / `/reset-password`）。
- 工具组：保留 `finance` 工具组（购买记录、发票文件）；workbench 不再被 `tool-navigation.tsx` import，registry 不会再被 `project_management` 自注册。
- 平台 navigation：仪表盘 `/`、用户设置 `/settings`、用户管理 `/admin` 不变。

## 调用了哪些 API

本轮仅删除前端代码，未新增、未修改任何前端 API 调用。

## 新增或修改了哪些测试

未新增测试。任务包同意：

> 如 Playwright 环境仍因 Chromium 系统库缺失无法执行，不要求新增 E2E；但 report 中必须说明本轮是删除旧工具，构建通过即为主要前端验证。

构建通过即为本轮主要前端验证。已删除的两份项目管理 Playwright 见上方表格。

## 校验命令与真实结果

```bash
docker compose exec -T frontend bun run build
```

结果：**通过**（exit 0，5.48s）。完整真实输出：

```
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
transforming...
✓ 2222 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                     0.57 kB │ gzip:   0.34 kB
dist/assets/index-B3Vft-ph.css                     67.66 kB │ gzip:  11.81 kB
dist/assets/finance.invoice-files-B-H-KhdU.js       0.17 kB │ gzip:   0.16 kB
dist/assets/finance.purchase-records-DohMqtNt.js    0.17 kB │ gzip:   0.16 kB
dist/assets/index-DvunmQYz.js                       0.36 kB │ gzip:   0.27 kB
dist/assets/recover-password-B58qMBEn.js            1.35 kB │ gzip:   0.70 kB
dist/assets/reset-password-DesjCsn9.js              2.01 kB │ gzip:   0.88 kB
dist/assets/login-CSY8ai4-.js                       3.22 kB │ gzip:   1.45 kB
dist/assets/settings-CnY6pRdy.js                    7.09 kB │ gzip:   2.34 kB
dist/assets/admin-CF6QoF6E.js                      71.28 kB │ gzip:  19.37 kB
dist/assets/index-guFmDHxQ.js                     781.12 kB │ gzip: 234.11 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 5.48s
```

观察：

- 模块总数从 Round 003 报告记录的 2237 降到 2222（少 15 个模块），与 workbench/Items 删除规模一致（6 + 5 + 1 路由 + 3 hooks/types/schemas 子目录及内部桥接 = 约 15 个 TS 文件）。
- 不再生成 `dist/assets/items-*.js` 入口 chunk；不再生成任何 `workbench` 相关 chunk。
- chunk size 警告与本轮无关（既存代码切分问题，与 Round 003 报告同源）。
- TypeScript 编译 (`tsc -p tsconfig.build.json`) 与 vite build 均无错误，确认 Items/* 删除后无外部模块再引用 `@/tools/workbench/project_management/...`。

## rg workbench / project_management 检查结果

执行：

```bash
rg -n "workbench|project_management|project-management|projectManagement" frontend
```

实际结果（删除后）：

```
frontend/src/tools/registry.ts:35:  /** Group name, e.g., "workbench" */
```

仅剩一条命中：

- `frontend/src/tools/registry.ts:35` 是 `ToolModuleConfig.group` 字段的 JSDoc 注释（举例字符串 `"workbench"`），非真实引用；不影响运行时与构建。
- `registry.ts` 不在任务包 `允许修改` 列表内，按任务包 `如果只剩文档或历史说明，可以在报告中说明` 处理；建议后续维护轮次顺手更新为 `e.g., "finance"`。

无前端业务代码、路由、测试再 import / 引用 workbench 或 project_management。

`routeTree.gen.ts` 全文核对：未发现 `Items` / `items.tsx` / `LayoutItemsRoute` / `/items` 任意片段。

## 前端越界自检

| 检查项 | 结论 |
|--------|------|
| 是否动了 `backend/**` | ❌ 没有 |
| 是否动了 `skills/**` | ❌ 没有 |
| 是否动了 `frontend/src/tools/finance/**` | ❌ 没有，finance 模块未触碰 |
| 是否动了 `frontend/src/routes/_layout/finance.*` | ❌ 没有 |
| 是否动了 `frontend/src/i18n/**` | ❌ 没有，构建未要求修改 i18n（admin.ts 中 items 文案保持原状，列入未完成项） |
| 是否手动修改 `frontend/src/routeTree.gen.ts` | ❌ 没有，由 TanStack Router 在 `bun run build` 中自动刷新 |
| 是否动了 Round 003 / Round 005 / Round 008 文档和代码 | ❌ 没有 |
| 是否动了任务包未授权且与 workbench 删除无关的文件 | ❌ 没有；`items.tsx` / `components/Items/` / `tests/items/` 的删除已与用户确认 |
| 是否影响 finance 工具组（购买记录、发票文件） | ❌ 不影响，构建产物仍包含 `finance.invoice-files-*.js`、`finance.purchase-records-*.js` |
| 是否影响平台组（仪表盘、个人设置、用户管理） | ❌ 不影响，`buildPlatformNavigation` 未触碰；`/`、`/settings`、`/admin` 路由保留 |
| 是否新增视觉风格 | ❌ 没有，纯删除 |

## 联调检查（前端已验证项 / 未验证项）

### 已验证（构建层）

- `tsc -p tsconfig.build.json` 严格类型检查通过。
- vite 生产构建成功，2222 modules transformed。
- `routeTree.gen.ts` 重新生成后不含 `/items` 任何形式（已 Read 全文核对）。
- `tool-navigation.tsx` 仅保留 finance 两个 import，未引用 workbench。
- finance 两个 chunk (`finance.invoice-files-*.js`、`finance.purchase-records-*.js`) 仍存在。

### 未验证（受 Playwright 环境阻塞）

- 浏览器实际渲染下：侧边栏不再展示 `Workbench` / `工作台` / `项目管理` / `Project Management`。
- 浏览器实际渲染下：访问 `/items` 进入 NotFound / 路由未匹配状态。
- 浏览器实际渲染下：财务工具组（购买记录、发票文件）入口仍可点击进入页面。
- 用户管理"删除用户"提示仍含 `"All items associated with this user..."`，UI 测试未变更（i18n 未在本轮修改）。

Playwright 仍因前端容器缺 Chromium 系统库无法跑通（与 Round 003 frontend-report 同根因诊断），任务包同意"构建通过即为主要前端验证"，故未追加 E2E。

## 未完成项（首次交付）

- ❌ `frontend/src/components/Pending/PendingItems.tsx` 已成孤儿（只被被删的 `ProjectManagementPage` 引用）；任务包 `允许修改` 不含 `Pending/`，本轮未主动删除，留待后续清理轮次。
- ❌ `frontend/tests/utils/random.ts` 中 `randomItemTitle`、`randomItemDescription` 现为未使用导出；不影响构建，未主动删除。
- ✅ `frontend/src/i18n/dictionaries/en-US/admin.ts` 中 `"All items associated with this user..."` 已在 [后续补丁](#后续补丁remove_workbench-收尾) 中处理。
- ❌ `frontend/src/tools/registry.ts:35` JSDoc 注释 `e.g., "workbench"` 未改；该文件不在任务包 `允许修改` 列表，按任务包"剩文档或历史说明可在报告中说明"处理。
- ❌ Playwright 自动化用例未跑：前端容器缺 Chromium 系统库（与 Round 003 同根因），任务包同意构建通过即为主要前端验证。

## 后续补丁（remove_workbench 收尾）

> 本节对应 Round 006 后续派单 `remove_workbench 收尾`，闭合首次交付的两项遗留：(1) 三语言 admin 字典的 "items / 项目 / 項目" 残留；(2) workbench 删除的端到端验证用例。

### 输入物路径（增量）

- `docs/rounds/round-006/frontend-report.md`（首次交付文本，本节追加）
- `frontend/src/i18n/dictionaries/zh-CN/admin.ts`
- `frontend/src/i18n/dictionaries/en-US/admin.ts`
- `frontend/src/i18n/dictionaries/zh-TW/admin.ts`
- `frontend/src/components/Admin/DeleteUser.tsx`（已 Read，未改 — `t("admin.deleteUserDescription")` 已在原代码中对接 i18n）

### 修改文件

| 路径 | 修改内容 |
|------|----------|
| `frontend/src/i18n/dictionaries/zh-CN/admin.ts` | `deleteUserDescription` 由 `"与该用户关联的所有项目将被永久删除，此操作不可撤销。"` 改为 `"该用户相关数据将被永久删除。此操作无法撤销。"`。 |
| `frontend/src/i18n/dictionaries/en-US/admin.ts` | `deleteUserDescription` 由 `"All items associated with this user will be permanently deleted. This action cannot be undone."` 改为 `"Data associated with this user will be permanently deleted. This action cannot be undone."`。 |
| `frontend/src/i18n/dictionaries/zh-TW/admin.ts` | `deleteUserDescription` 由 `"與該使用者關聯的所有項目將被永久刪除，此操作無法撤銷。"` 改为 `"與此使用者相關的資料將被永久刪除。此操作無法復原。"`。 |

> `DeleteUser.tsx` 仅消费 `t("admin.deleteUserDescription")` 字典键、未硬编码任何英文，因此组件代码无需变动；三语字典更新后 UI 会立即一致。

### 新增文件

| 路径 | 说明 |
|------|------|
| `frontend/tests/platform/remove-workbench/index.spec.ts` | 新增 6 个 Playwright 用例：sidebar 在三种 locale 下都不再展示 `工作台` / `Workbench` / `项目管理` / `Project Management` / `項目管理` / `專案管理`；`/items` 路由不再渲染项目管理专属元素（`Add Item` / `添加项目` / `Items Management` / `项目管理` heading 全部不应存在）；`/admin` 删除用户确认弹窗在 en-US / zh-CN 下不再含 `items` / `项目`，且分别匹配新的中性化文案。 |

测试设计要点：
- 复用 `chromium` project 的 `storageState` 完成超级管理员登录。
- `setLocale(page, locale)` 通过 `localStorage.setItem("app_locale", l)` + `page.reload()` 切换 i18n（与 `tests/i18n.spec.ts` 同模式）。
- 删除用户用例使用 `randomEmail()` / `randomPassword()` 现场创建用户、定位行 → 打开行操作菜单 → 点 `Delete User` / `删除用户` → 仅断言确认弹窗内容，不真正执行 `Delete`，避免破坏数据库前置数据。
- 用 `await expect(...).toHaveCount(0)` 替代 `not.toBeVisible()` 表达"该元素不存在"，避免 Strict mode 多元素时的歧义。

### 路由 / 工具组注册

补丁不动路由、工具组、registry。

### 调用了哪些 API

仅 Playwright 用例内部调用既有 `UsersService.createUser` / `UsersService.deleteUser`（前端代码层未新增请求）；i18n 字典更新不引入任何 API 调用。

### 校验命令与真实结果

#### 1. 前端构建

```bash
docker compose exec -T frontend bun run build
```

结果：**通过**（exit 0，4.47s）。完整真实输出：

```
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
transforming...
✓ 2222 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                     0.57 kB │ gzip:   0.34 kB
dist/assets/index-B3Vft-ph.css                     67.66 kB │ gzip:  11.81 kB
dist/assets/finance.invoice-files-tN6xFyOE.js       0.17 kB │ gzip:   0.16 kB
dist/assets/finance.purchase-records-D0I9VaMo.js    0.17 kB │ gzip:   0.16 kB
dist/assets/index-COyAotgP.js                       0.36 kB │ gzip:   0.27 kB
dist/assets/recover-password-DCTuAHiq.js            1.35 kB │ gzip:   0.70 kB
dist/assets/reset-password-bqHGv3hf.js              2.01 kB │ gzip:   0.88 kB
dist/assets/login-DgsAL-3q.js                       3.22 kB │ gzip:   1.45 kB
dist/assets/settings-DAGpuN83.js                    7.09 kB │ gzip:   2.34 kB
dist/assets/admin-DMgXjIfT.js                      71.28 kB │ gzip:  19.37 kB
dist/assets/index-BsAdLEBn.js                     781.09 kB │ gzip: 234.08 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.47s
```

观察：

- 模块总数 2222，与首次交付一致；`admin-*.js` chunk 大小 71.28 kB（与首次交付完全相同），`index-*.js` 主 bundle 仅减 0.03 kB（gzip 234.08 vs 234.11）—— 字典字符串置换不改变模块数量、chunk 边界与依赖图。
- TypeScript 严格类型检查（`tsc -p tsconfig.build.json`）通过；新增测试文件位于 `tests/`，不进入 `tsconfig.build.json` 的 `include`，但 `tests/tsconfig.json` 路径若纳入构建会同时检测；本机运行 `bun run build` 已覆盖工程主体类型检查。

#### 2. Playwright 测试

任务包指定命令：

```bash
docker compose exec -T frontend bun run test -- tests/platform/remove-workbench/index.spec.ts --reporter=line --timeout=15000
```

实际执行结果：**未能进入用例阶段，被外层 `timeout 90s` 强杀**。

| 字段 | 值 |
|------|-----|
| 真实命令 | `timeout 90 docker compose exec -T frontend bun run test -- tests/platform/remove-workbench/index.spec.ts --reporter=line --timeout=15000` |
| 真实退出码 | `124`（外层 `timeout` 强杀，与 Round 003 / 005 / 006 系列完全同源） |
| 真实输出 | 仅一行 `$ bun x playwright test tests/platform/remove-workbench/index.spec.ts "--reporter=line" "--timeout=15000"` 之后零输出 |

#### 3. Playwright 阻塞根因复核

诊断命令：

```bash
docker compose exec -T frontend bash -c \
  'ldd /root/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome 2>/dev/null | grep "not found" | head -10'
```

输出（截取，仍报告大量缺失，与 Round 003 / 006 首次交付一致）：

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
```

结论：本补丁的 `index.spec.ts` 编写正确（语法、selector、`storageState` / locale 设置均沿用 i18n.spec.ts / admin.spec.ts 验证过的模式），但**前端容器缺 Chromium 系统库（≥20 个）**导致浏览器进程启动后挂起、无 stderr 输出、外层 `timeout` 强杀（exit 124），与 Round 003 frontend-report `### 3. Playwright 阻塞根因再次诊断` 章节同根因。该问题需要在 `frontend/Dockerfile` 通过 `apt-get install`（`libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcb1 libxkbcommon0 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libasound2 libexpat1` 一组）或 `bunx playwright install --with-deps chromium` 处理，**超出本补丁前端代码范围**。

#### 4. 字典残留 grep 复核

```bash
rg -n "items" frontend/src/i18n/dictionaries
rg -n "项目|項目|專案" frontend/src/i18n/dictionaries
```

实际结果：

- `items` 在 `frontend/src/i18n` 全目录命中 0 行（locales.ts 中 `localStorage.getItem` 是函数名，含 `Item` 但非用户文案，已经过 `-i` / 中性化场景外的细分核对）。
- `项目|項目|專案` 仍命中 4 行：`zh-CN/finance.ts:9 / 95` `其他项目费用` 与 `zh-TW/purchaseRecords.ts:7 / 87` `其他專案費用` —— 均为财务 `other_project` 大类标签，与 workbench / Items 无关，**不能动**。

补丁后无 admin 文案再含 "items" / "项目" / "項目"。

### 联调检查（前端已验证项 / 未验证项）

#### 已验证

- TypeScript 严格构建通过，三语字典字面量替换未引入类型/键错位。
- 首次交付未通过的"工具自注册关联静态字符串"未受影响（`registry.ts` / `tool-navigation.tsx` / finance index 未触碰）。
- `DeleteUser.tsx` 通过 `t("admin.deleteUserDescription")` 消费字典键，不存在硬编码英文。
- `tests/platform/remove-workbench/index.spec.ts` 文件创建成功，按 `tests/i18n.spec.ts` / `tests/admin.spec.ts` 既有约定编写（`storageState` 复用、`getByRole`、`page.evaluate(localStorage.setItem)`）。

#### 未验证（受 Playwright 环境阻塞）

- 浏览器实际渲染下：sidebar 在 zh-CN / en-US / zh-TW 都不再出现 `工作台` / `Workbench`、`项目管理` / `Project Management` / `項目管理` / `專案管理`。
- 浏览器实际渲染下：访问 `/items` 进入 NotFound（或 fallback）状态。
- 浏览器实际渲染下：删除用户确认弹窗内容已切到中性化文案。
- `playwright/.auth/user.json` 在补丁回归运行中是否仍可正常生成（与 Round 003 同根因阻塞）。

### 前端越界自检

| 检查项 | 结论 |
|--------|------|
| 是否仅修改任务包 `允许修改` 范围内文件 | ✅ 是；本补丁触碰：`frontend/src/i18n/dictionaries/{zh-CN,en-US,zh-TW}/admin.ts`、`frontend/tests/platform/remove-workbench/index.spec.ts`（新增）、`docs/rounds/round-006/frontend-report.md`（追加本节）。 |
| 是否动了 `backend/**` | ❌ 没有 |
| 是否动了 `skills/**` | ❌ 没有 |
| 是否动了 `frontend/src/tools/**` | ❌ 没有 |
| 是否动了 `frontend/src/components/**` | ❌ 没有（仅 Read 了 `Admin/DeleteUser.tsx` 确认 i18n 接入，无修改） |
| 是否动了 `frontend/src/routes/**` / `routeTree.gen.ts` | ❌ 没有 |
| 是否动了非 `admin.ts` 的字典 | ❌ 没有；`finance.ts` / `purchaseRecords.ts` 中的 `其他项目费用` / `其他專案費用` 是大类标签，不属于本补丁清理目标 |
| 是否新增视觉风格 / 组件 | ❌ 没有，纯文案中性化 |
| 是否影响 finance 工具组 | ❌ 不影响，构建产物 chunk 与首次交付一致 |
| 是否影响平台组（仪表盘 / 个人设置 / 用户管理） | ❌ 仅"用户管理删除确认文案"由"全部项目"改为"相关数据"，体感一致 |
| 是否手动修改 `routeTree.gen.ts` | ❌ 没有 |
| 是否动了 Round 003 / Round 005 / Round 008 文件 | ❌ 没有 |

### 后续补丁未完成项

- ❌ `frontend/src/components/Pending/PendingItems.tsx` 仍是孤儿组件（仍不在补丁 `允许修改` 列表，未删除）。
- ❌ `frontend/tests/utils/random.ts` 中 `randomItemTitle` / `randomItemDescription` 仍是未使用导出（不在补丁 `允许修改` 列表）。
- ❌ `frontend/src/tools/registry.ts:35` 注释 `e.g., "workbench"` 仍未改（不在补丁 `允许修改` 列表）。
- ❌ Playwright 6 个新用例未真实跑通：根因仍为前端容器 Chromium 系统库缺失（详见上文 `### 3. Playwright 阻塞根因复核`）；按任务包同意"如挂起照实说明"，本节如实记录命令、退出码 124、零输出与 ldd 缺失库列表，**未谎称通过**。修复手段属于容器编排范围，建议在独立 DevOps 轮次中执行 `apt-get install`/`playwright install-deps` 后重跑本 spec。
