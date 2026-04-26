# Round 005 Frontend Report - invoice_matching

## 修订记录

### FE-INVOICE-MATCHING-FIX-001（2026-04-26）：第四 tab 由「异常」改名为「已取消」

**问题**：初版第 4 个 tab 显示文案为「异常 / Exception / 異常」（i18n key `tabs.exception`），但内部绑定的是 `MatchList status="cancelled"`，仅展示 `cancelled` 匹配。design.md 中「异常视图」实际指三类聚合：「无发票的购买记录」「confirmed 但未分摊的发票」「弱候选」。两者语义不一致，会误导用户把「我自己取消的匹配」当成系统异常。

**保守修复策略**：本轮后端没有提供「异常视图」专用聚合 API（design.md 中也未在 Round 005 列入 backend 必交付 API），不能冒充。修复方案：

1. 第 4 个 tab 文案改为「已取消 / Cancelled / 已取消」；i18n key `tabs.exception` → `tabs.cancelled`；UI 仍绑定 `MatchList status="cancelled"`，与文案语义对齐。
2. 三语字典 (`zh-CN/finance.ts`、`en-US/invoiceMatching.ts`、`zh-TW/invoiceMatching.ts`) 同步替换。
3. Playwright 用例（`tests/finance/invoice_matching/index.spec.ts`）相关断言由「异常 / Exception / 異常」改为「已取消 / Cancelled / 已取消」；测试名同步。
4. 真正的「异常视图」（无发票购买记录、孤立发票、弱候选）显式列入未完成项，需要后端补 `/anomalies` 聚合 API 后再实现，不再用 cancelled 顶替。

**改动文件**：

| 路径 | 改动 |
|------|------|
| `frontend/src/tools/finance/invoice_matching/components/InvoiceMatchingPage.tsx` | TabsTrigger key 由 `tabs.exception` 改为 `tabs.cancelled` |
| `frontend/src/i18n/dictionaries/zh-CN/finance.ts` | `invoiceMatching.tabs.exception: "异常"` → `invoiceMatching.tabs.cancelled: "已取消"` |
| `frontend/src/i18n/dictionaries/en-US/invoiceMatching.ts` | `tabs.exception: "Exception"` → `tabs.cancelled: "Cancelled"` |
| `frontend/src/i18n/dictionaries/zh-TW/invoiceMatching.ts` | `tabs.exception: "異常"` → `tabs.cancelled: "已取消"` |
| `frontend/tests/finance/invoice_matching/index.spec.ts` | 三处 `异常`/`Exception`/`異常` 断言改为 `已取消`/`Cancelled`/`已取消`,测试用例名同步 |
| `docs/rounds/round-005/frontend-report.md` | 增加本节 + 同步下文 i18n / 测试 / 未完成项 |

**FIX-001 校验命令与真实结果**

```bash
docker compose exec -T frontend bun run build
docker compose exec -T frontend bunx tsc --noEmit -p tsconfig.json
docker compose exec -T frontend bun run test -- tests/finance/invoice_matching/index.spec.ts --reporter=line --timeout=15000
```

| 命令 | 结果 |
|------|------|
| `bun run build` | ✅ 通过(exit 0,5.64s),新 chunk `finance.invoice-matching-W934_fQc.js` 0.17 kB,所有重命名键无引用错误 |
| `bunx tsc --noEmit -p tsconfig.json` | ✅ 通过(exit 0,无类型错误输出) |
| `bun run test -- ... --reporter=line --timeout=15000` | ❌ 阻塞超时,与初版报告一致;已二次复现 `bunx playwright test --list` 在 `timeout 30s` 下 EXIT=124,容器仍缺 25 项 Chromium 系统库且 `which npx` 为空,bun-node-fallback 替身无法 spawn Chromium |

FIX-001 仅修改文案/i18n key/测试断言,未触碰任何业务逻辑或路由结构,代码层校验充分通过;e2e 阻塞与初版同因,记录于下文「未完成项」。

---

## 输入物路径

- `docs/rounds/round-005/requirements.md`
- `docs/rounds/round-005/design.md`
- `docs/rounds/round-005/test-plan.md`
- `docs/rounds/round-005/tasks.md`
- `docs/rounds/round-005/dispatch-frontend.md`
- `docs/rounds/round-005/backend-report.md`
- `backend/app/modules/finance/invoice_matching/router.py`
- `backend/app/modules/finance/invoice_matching/models.py`
- `backend/app/modules/finance/invoice_matching/service.py`
- `backend/app/modules/finance/invoice_matching/constants.py`
- `frontend/src/tools/finance/purchase_records/`（api / types / hooks / components / index.ts）
- `frontend/src/tools/finance/invoice_files/`（api / types / hooks / components / index.ts）
- `frontend/src/tools/registry.ts`
- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/i18n/`（I18nProvider.tsx, dictionaries/zh-CN/finance.ts, dictionaries/en-US/index.ts, dictionaries/zh-TW/index.ts 等）
- `frontend/src/routes/_layout/finance.purchase-records.tsx`
- `frontend/src/routes/_layout/finance.invoice-files.tsx`
- `frontend/src/routeTree.gen.ts`
- `frontend/tests/finance/invoice_files/index.spec.ts`
- `frontend/tests/utils/{user.ts, privateApi.ts, random.ts}`
- `frontend/playwright.config.ts`

## 修改文件汇总

| 路径 | 类型 |
|------|------|
| `frontend/src/tools/finance/invoice_matching/types.ts` | 新增 |
| `frontend/src/tools/finance/invoice_matching/api.ts` | 新增 |
| `frontend/src/tools/finance/invoice_matching/index.ts` | 新增 |
| `frontend/src/tools/finance/invoice_matching/hooks/useInvoiceMatching.ts` | 新增 |
| `frontend/src/tools/finance/invoice_matching/components/InvoiceMatchingPage.tsx` | 新增 |
| `frontend/src/tools/finance/invoice_matching/components/UnmatchedList.tsx` | 新增 |
| `frontend/src/tools/finance/invoice_matching/components/CandidateList.tsx` | 新增 |
| `frontend/src/tools/finance/invoice_matching/components/MatchList.tsx` | 新增 |
| `frontend/src/routes/_layout/finance.invoice-matching.tsx` | 新增 |
| `frontend/tests/finance/invoice_matching/index.spec.ts` | 新增 |
| `frontend/src/i18n/dictionaries/en-US/invoiceMatching.ts` | 新增 |
| `frontend/src/i18n/dictionaries/zh-TW/invoiceMatching.ts` | 新增 |
| `frontend/src/i18n/dictionaries/zh-CN/finance.ts` | 修改（追加 `invoiceMatching` 块） |
| `frontend/src/i18n/dictionaries/en-US/index.ts` | 修改（合入 `invoiceMatching`） |
| `frontend/src/i18n/dictionaries/zh-TW/index.ts` | 修改（合入 `invoiceMatching`） |
| `frontend/src/config/tool-navigation.tsx` | 修改（追加 `import "@/tools/finance/invoice_matching"`） |
| `frontend/src/routeTree.gen.ts` | 由 TanStack Router 插件自动重新生成（人工只新增了对应路由文件） |
| `docs/rounds/round-005/frontend-report.md` | 新增 |

## 新增页面 / 路由

- 路由：`/_layout/finance/invoice-matching`，文件 `frontend/src/routes/_layout/finance.invoice-matching.tsx`，使用 `toolRegistry.getTool("invoice_matching")` 取出注册组件渲染。
- 工具注册：`frontend/src/tools/finance/invoice_matching/index.ts` 通过 `registerTool` 自注册到 `finance` 工具组：
  - `name: "invoice_matching"`
  - `group: "finance"`
  - `route.path: "/finance/invoice-matching"`
  - `route.titleKey: "finance.invoiceMatching.title"`
  - `navigation.titleKey: "finance.invoiceMatching.title"`
  - `navigation.icon: Link2`
  - `navigation.requiresSuperuser: false`
- 在 `frontend/src/config/tool-navigation.tsx` 增加 `import "@/tools/finance/invoice_matching"` 触发自注册，未改动其他工具入口。

## 新增 API 调用

`BASE_URL = "/api/v1/finance/invoice-matching"`，所有调用使用既有 `__request(OpenAPI, …)`，未引入新 HTTP 客户端：

| 函数 | 方法 | URL | 说明 |
|------|------|-----|------|
| `getMatchSummary()` | GET | `/summary` | 顶部汇总卡片 |
| `listUnmatchedPurchaseRecords()` | GET | `/unmatched-purchase-records` | 待匹配 tab |
| `listAvailableInvoices()` | GET | `/available-invoices` | （类型已建模，当前 UI 未直接消费，作为后续扩展点） |
| `listCandidates(purchaseRecordId)` | GET | `/candidates?purchase_record_id=…` | 候选发票列表，后端对不可匹配 PR 抛 400 ValueError |
| `listMatches({status})` | GET | `/matches` | 已匹配 / 需复核 / 已取消 tab |
| `confirmMatch({purchase_record_id, invoice_file_id})` | POST | `/confirm` | 普通用户对单条 PR + 单张候选发票确认 |
| `cancelMatch(matchId)` | POST | `/{match_id}/cancel` | 普通用户取消匹配 |
| `reconfirmMatch(matchId)` | POST | `/{match_id}/reconfirm` | 普通用户对 `needs_review` 重新确认 |

候选 / 匹配请求结果直接对应后端 `CandidateInvoice` / `InvoiceMatchPublic`，TS 类型在 `types.ts` 一一映射（包括 `score`, `score_breakdown`, `level`, `allocated_amount`, `remaining_amount`, `review_reason` 等）。

## i18n 接入说明

- 字典策略沿用现有 finance 工具组：
  - `zh-CN/finance.ts`：在原文件追加 `invoiceMatching: {...}` 同级块，避免新增独立文件破坏既有结构。
  - `en-US/invoiceMatching.ts`、`zh-TW/invoiceMatching.ts`：新增独立文件（与 `purchaseRecords.ts`、`invoiceFiles.ts` 一致），并在对应 `index.ts` 中 `import` 后挂在 `finance.invoiceMatching` 下。
- 字典覆盖范围：
  - `title` / `subtitle` / `tabs.{unmatched,matched,needsReview,cancelled}`（FIX-001 已将 `tabs.exception` 重命名为 `tabs.cancelled`）
  - `summary.{confirmed,needsReview,cancelled,unmatched,availableInvoices}`
  - `purchaseStatus.{submitted,approved}`
  - `status.{confirmed,needs_review,cancelled}`
  - `level.{strong,weak,low}`、`scoreCategory.{amount,currency,date,text,keyword}`
  - `fields.{purchaseDate,amount,seller,invoiceDate,invoiceAmount,allocatedAmount,remainingAmount,purchaseRecordId,invoiceFileId,reviewReason,createdAt,confirmedAt,cancelledAt}`
  - `actions.{confirm,confirming,cancel,cancelling,reconfirm,reconfirming,showCandidates,hideCandidates,scoreBreakdown,toggleBreakdown}`
  - `empty.{unmatchedTitle,unmatchedDescription,candidates,confirmed,needs_review,cancelled}`
  - `messages.{confirmSuccess,confirmFailed,cancelSuccess,cancelFailed,reconfirmSuccess,reconfirmFailed}`
  - `unknownInvoice` / `unknownOrder` / `candidateBlocked` / `scoreLabel` / `scoreBreakdownTitle` / `scoreBreakdownEmpty` / `adminReadOnlyHint`
- `tools/registry.ts` 中 `_groupNameMap.finance = "finance.groupName"` 已在 Round 003 落地，本轮直接复用，未再调整。
- 未新增独立 i18n 系统、未新增 hook、未替换 `useI18n()` 实现。

## UI / 业务实现要点

- `InvoiceMatchingPage.tsx`：
  - 顶部 `useMatchSummaryQuery()` 拉取汇总，5 个 `Card` 分别展示「已匹配 / 需复核 / 已取消 / 待匹配购买记录 / 可匹配发票」，均带 `data-testid` 方便测试。
  - 4 个 Tabs：`unmatched`（→`UnmatchedList`）、`matched`（→`MatchList status="confirmed"`）、`needs_review`（→`MatchList status="needs_review"`）、`cancelled`（→`MatchList status="cancelled"`，文案为「已取消 / Cancelled / 已取消」，**不再冒充 design.md 中的「异常视图」**，原因见 FIX-001 与未完成项）。
  - 通过 `useAuth().user.is_superuser` 取得 `isAdmin`：管理员进入页面会额外渲染「只读提示」卡片，且不会在子组件中渲染确认 / 取消 / 重新确认按钮。
- `UnmatchedList.tsx`：
  - 拉取 `listUnmatchedPurchaseRecords`，每条 PR 渲染为 `Card`，标题/金额/币种/状态徽章。
  - 点击「查看候选发票」展开对应 `<CandidateList purchaseRecord />`，再次点击收起；展开按钮使用 `data-testid="toggle-candidates"`。
- `CandidateList.tsx`：
  - 调用 `useCandidatesQuery(purchaseRecord.id)`，`retry: false`，让后端 400（PR 不可匹配）一次返回即止。
  - 错误态渲染独立 `Card` 显示「当前购买记录不可匹配 / This purchase record is not eligible for matching」+ 后端错误文案，命中需求中的 400 兜底。
  - 每个候选项展示：`invoice_number` / 等级 Badge（strong / weak / low）/ 评分 Badge / 销售方 / 发票日期 / 金额 / 已分摊 / 剩余。
  - 点击「评分解释」展开 `score_breakdown` 字典，遍历 `Object.entries` 用 `t("finance.invoiceMatching.scoreCategory.<key>")` 翻译评分项名称（amount / currency / date / text / keyword）。
  - 普通用户在每个候选项右侧渲染「确认匹配」按钮，调用 `useConfirmMatchMutation`；管理员不渲染该按钮。
- `MatchList.tsx`：
  - 按 `status` 拉取 `useMatchesQuery(status)`，每条匹配渲染 `Card`，含 `purchase_record_id` / `invoice_file_id`（monospace 显示便于排查）/ 状态 Badge / 评分 Badge / 复核原因（若有）/ 时间戳。
  - 普通用户：`needs_review` 渲染「重新确认」按钮（→ `useReconfirmMatchMutation`），非 cancelled 渲染「取消匹配」按钮（→ `useCancelMatchMutation`）。
  - 管理员：上述按钮全部隐藏，仅查看，符合任务包「不显示代确认 / 取消 / 重新确认按钮」的要求。
- TanStack Query：
  - `invoiceMatchingQueryKey = ["invoice-matching"]`，summary / unmatched / available-invoices / matches / candidates 分别带子键。
  - 任意 mutation 成功后调用 `queryClient.invalidateQueries({ queryKey: invoiceMatchingQueryKey })`，让汇总卡片、待匹配列表、各 tab 的 matches 都自动刷新。
- 未新增任何 Zod schema：当前 UI 不渲染表单输入，所有展示都基于服务端返回；如未来加入「自定义评分批注」等表单需求，可补 `schemas.ts`。

## 新增测试

`frontend/tests/finance/invoice_matching/index.spec.ts` 共 12 条用例：

主 `describe`（沿用默认 admin storageState）：

1. `发票匹配页面可正常打开并显示标题`：访问 `/finance/invoice-matching`，断言 heading「发票匹配」与 subtitle「将购买记录与已确认发票进行关联」可见。
2. `从侧边栏可进入发票匹配页面`：先进入 `/`，按需展开「财务」组，点击 `link[name="发票匹配"]`，确认 URL 落到 `/finance/invoice-matching`。
3. `待匹配 / 已匹配 / 需复核 / 已取消 四个 tab 都存在`。
4. `已匹配 tab 切换可见空状态文案`（默认无匹配 → 「暂无已匹配的记录」）。
5. `需复核 tab 切换可见空状态文案`（→ 「暂无需复核的匹配」）。
6. `已取消 tab 切换可见空状态文案`（→ 「暂无已取消的匹配」）。
7. `汇总卡片显示已匹配 / 需复核 / 已取消 / 待匹配 / 可匹配发票`：通过 `data-testid` 定位 5 张卡片。
8. `管理员登录时显示只读提示，不展示代用户操作按钮`：默认 storageState 为 admin，断言只读提示卡片可见。
9. `英文 i18n 接入正确`：写入 `localStorage.app_locale = "en-US"` 并 reload，断言 heading「Invoice Matching」与 4 个英文 tab 名。
10. `繁体中文 i18n 接入正确`：写入 `zh-TW`，断言 heading「發票匹配」、tab「需複核」「已取消」。

`describe("普通用户视角")`（独立 `storageState: { cookies: [], origins: [] }` + 临时用户 `createUser` + `logInUser`）：

11. `普通用户看不到管理员只读提示`。
12. `普通用户在待匹配 tab 看到空状态`（新建用户必然空）。
13. `汇总卡片对普通用户也可见`。

测试覆盖任务包 `test-plan.md` 中的：
✅ 财务工具组出现 `发票匹配`（用例 #2）
✅ 页面可以打开（用例 #1）
✅ 待匹配、已匹配、需复核、已取消 tabs 存在（用例 #3，FIX-001 后第 4 tab 文案由「异常」改为「已取消」，详见上文修订记录）
✅ 汇总卡片渲染（用例 #7）
✅ 管理员看得到所有匹配但没有代确认按钮（用例 #8 + 普通用户 vs 管理员对比，普通用户用例 #11）
✅ i18n 已完成时，页面文案走翻译（用例 #9, #10）
⚠️ 候选列表显示评分和评分解释 / 已分摊 / 剩余 / 普通用户逐条确认 / 取消 — 因受 Playwright 启动阻塞（见下），且这些场景需要预置「已确认发票 + 已提交 PR」前置数据，本轮未通过浏览器实跑覆盖，UI 路径已通过组件代码与构建验证。后续可在 backend 提供测试夹具后用 `privateApi` 注入数据。

## 校验命令与真实结果

### 1. 前端构建

```bash
docker compose exec -T frontend bun run build
```

结果：**通过**（exit 0，5.33s）。完整真实输出：

```
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
transforming...
✓ 2235 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                     0.57 kB │ gzip:   0.34 kB
dist/assets/index-Bo4Z8_g2.css                     68.25 kB │ gzip:  11.93 kB
dist/assets/finance.invoice-files-CtEmlPJS.js       0.17 kB │ gzip:   0.16 kB
dist/assets/finance.purchase-records-DQrBaOp6.js    0.17 kB │ gzip:   0.16 kB
dist/assets/finance.invoice-matching-CAIyiYVk.js    0.17 kB │ gzip:   0.16 kB
dist/assets/index-DMwt73HS.js                       0.36 kB │ gzip:   0.27 kB
dist/assets/recover-password-BE0ApchO.js            1.35 kB │ gzip:   0.70 kB
dist/assets/reset-password-Bp_ddkwa.js              2.01 kB │ gzip:   0.88 kB
dist/assets/login-FtPbStWu.js                       3.04 kB │ gzip:   1.36 kB
dist/assets/settings-Bo82jEHJ.js                    7.10 kB │ gzip:   2.34 kB
dist/assets/admin-BJclxrSX.js                      71.28 kB │ gzip:  19.37 kB
dist/assets/index-C33zmHUf.js                     802.44 kB │ gzip: 238.46 kB
✓ built in 5.33s
```

> chunk size 警告与本轮无关（既存代码切分问题，已在 Round 003 备注）。
> `finance.invoice-matching` 自动产出对应 chunk，证明路由注册与代码切分正常。
> TypeScript 严格构建（`tsc -p tsconfig.build.json`）无错误，本轮新增 7 个 TS / TSX 文件全部通过类型检查。

### 2. Playwright 测试

任务包指定命令：

```bash
docker compose exec -T frontend bun run test -- tests/finance/invoice_matching/index.spec.ts --reporter=line
```

实际执行结果：**未能执行用例，被外层超时杀死（容器环境问题，与 Round 003 同源）**。

| 字段 | 值 |
|------|-----|
| 真实命令 | `docker compose exec -T frontend bun run test -- tests/finance/invoice_matching/index.spec.ts --reporter=line` |
| 第一次：通过 `bun run test` 间接调用 | `bun run test` → `npx playwright test`，npx 不在容器 PATH，立即返回 `sh: 1: npx: not found`，EXIT=127 |
| 第二次：直接调用 playwright 二进制 | `cd /app && ./node_modules/.bin/playwright test tests/finance/invoice_matching/index.spec.ts --reporter=line > /tmp/pw-out.log 2>&1` |
| 外层 timeout 设置 | 600s（实际等待 ≈540s 后强杀） |
| `/tmp/pw-out.log` 大小 | 0 bytes（playwright 启动后零输出） |
| 真实退出码 | 124（外层 `timeout` 强杀） |
| `./node_modules/.bin/playwright --version` | `Version 1.57.0`（二进制本身可用） |
| 即便仅 `--list` 也复现 | `timeout 60 ./node_modules/.bin/playwright test tests/i18n.spec.ts --list` 同样 EXIT=124，0 字节输出 |

### 3. Playwright 阻塞根因诊断

```bash
docker compose exec -T frontend sh -c 'ldd /root/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome 2>&1 | grep "not found"'
```

输出（共 25 项）：

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
libXrandr.so.2 => not found
libgbm.so.1 => not found
libcairo.so.2 => not found
libpango-1.0.so.0 => not found
libasound.so.2 => not found
```

附加观察：

- 容器内 `node` 实为 bun-fallback 包装 (`/usr/local/bun-node-fallback-bin/node`)，无完整 npm/npx 工具链；`bun run test` 脚本配置 `npx playwright test` 直接 EXIT=127。
- 改用 `./node_modules/.bin/playwright` 直接调用后，进程能加载但子进程在 spawn Chromium 时挂起（与 Round 003 一致）。
- 即使 `--list` 用例发现也挂起，可能是 Playwright 1.57 的测试发现阶段需要一次性预热 worker 进程（仍依赖于 node child_process），在 bun-node 包装下行为异常。
- 该问题与本轮新增代码无关：使用既有 `tests/i18n.spec.ts` 与 `tests/finance/invoice_files/index.spec.ts` 复现，行为完全相同。

**结论**：Playwright 仍因前端容器缺系统包（`libglib2.0-0`, `libnss3`, `libnss-util3`, `libdbus-1-3`, `libgio2.0-cil`, `libatk1.0-0`, `libatk-bridge2.0-0`, `libcups2`, `libexpat1`, `libxcb1`, `libxkbcommon0`, `libatspi2.0-0`, `libx11-6`, `libxcomposite1`, `libxdamage1`, `libxext6`, `libxfixes3`, `libxrandr2`, `libgbm1`, `libcairo2`, `libpango-1.0-0`, `libasound2`, `libnspr4`）以及 `npx` 工具链缺失，无法在容器内运行。需要在 `frontend/Dockerfile` 中追加 `apt-get install -y --no-install-recommends $( … )` 或者 `bunx playwright install --with-deps chromium`，并确保 `npx`（npm）也可用，超出本轮前端代码修复范围（属于环境/容器编排）。

## 越界自检

| 检查项 | 结论 |
|--------|------|
| 是否仅修改任务包 `允许修改` 范围内文件 | ✅ 是 |
| 是否动了 `backend/**` | ❌ 没有 |
| 是否动了 `skills/**` | ❌ 没有 |
| 是否动了无关前端工具（`purchase_records`, `invoice_files`, `admin`, `settings` 等） | ❌ 没有 |
| 是否引入新 i18n 系统 / 替换 `useI18n` | ❌ 没有，沿用既有 `I18nProvider.tsx` |
| 是否新增任何后端 API 路径 | ❌ 没有，仅消费已存在的 `/api/v1/finance/invoice-matching/*` |
| 是否手动篡改 `routeTree.gen.ts` | ❌ 没有，仅由 TanStack Router 插件因新增 `routes/_layout/finance.invoice-matching.tsx` 自动重生成 |
| 是否引入新视觉语言 / 新 UI 框架 | ❌ 没有，仅复用 `@/components/ui/*`（Card, Tabs, Button, Badge）+ lucide-react 既有图标 |
| 是否破坏其他工具自注册 | ❌ 没有，新工具自注册结构与既有两个 finance 工具一致 |
| 是否动了 `playwright.config.ts` / `auth.setup.ts` | ❌ 没有 |
| 是否对 `run_in_background` 跑过的 Playwright 进程残留 | ❌ 已 `TaskStop` 清理 |

## 联调检查（前端已验证项 / 未验证项）

### 已验证

- TypeScript 严格构建通过：本轮 7 个新 TS/TSX 文件 + 3 个 i18n 字典文件 + 1 个路由文件 + tool-navigation.tsx 全部通过 `tsc -p tsconfig.build.json` 检查。
- Vite 生产构建通过，新增 chunk `finance.invoice-matching-CAIyiYVk.js` 正常产出。
- 工具自注册结构对齐：`registerTool({ name, group, route, navigation })` 与 `purchase_records` / `invoice_files` 完全同形，TanStack Router 已自动重写 `routeTree.gen.ts`。
- 三种语言字典中 `finance.invoiceMatching.title`、`tabs.*`、`status.*`、`level.*`、`scoreCategory.*` 等 key 均已落地，可读性人工核对一致。
- 候选列表 400 兜底：`useCandidatesQuery` 设 `retry: false`，错误态在 `CandidateList` 中独立渲染「当前购买记录不可匹配」+ 后端 detail，避免假装「无候选」。

### 未验证（受 Playwright 环境阻塞）

- 浏览器实际渲染：sidebar 中「财务」组下 `发票匹配` 真实显示与点击导航。
- 浏览器实际渲染：4 个 tab 的内容切换与对应空状态文案。
- 真实端到端：登录普通用户 → 创建已确认发票 + 已提交购买记录 → 候选列表评分 / 已分摊 / 剩余金额展示 → 确认匹配 → 已匹配 tab 出现 → 取消匹配 → 已取消 tab 出现 → 后端关键字段变更 → 需复核 tab 出现 → 重新确认。
- i18n 切换后页面立刻刷新（`I18nProvider` `reload` 行为已在 Round 003 验证，本轮代码未改其行为，但本轮新键未通过浏览器渲染走查）。
- 真正运行 `tests/finance/invoice_matching/index.spec.ts` 12 条用例的通过情况。

## 未完成项

- ❌ **真正的「异常视图」未实现（FIX-001 显式记录）**：design.md 中「异常视图」定义为聚合三类「(1) 没有任何 active 匹配、且也没有 cancelled 历史的购买记录漏匹配；(2) confirmed 但未被任何匹配分摊或仅部分分摊的孤立发票；(3) 弱候选（low/weak level）的购买记录」。后端 Round 005 未交付 `/anomalies` 或等价聚合端点，前端不能凭 `cancelled` 数据冒充。本轮 FIX-001 已把第 4 tab 改为「已取消」，避免误导用户。下一轮需要后端先实现聚合 API（建议 `GET /api/v1/finance/invoice-matching/anomalies?type=missing_invoice|orphan_invoice|weak_match`），前端再扩展第 5 个 tab 或独立面板承载。
- ❌ `tests/finance/invoice_matching/index.spec.ts` 真实跑通：受前端容器 25 项 Chromium 系统库缺失 + `npx` 不可用阻塞，与 Round 003 描述完全同源，本轮前端代码层无解，需要容器/CI 维护方在 `frontend/Dockerfile` 安装系统依赖与 npm 工具链后重跑。
- ❌ 候选列表「评分 / 评分解释 / 已分摊 / 剩余」与「确认 / 取消 / 重新确认」交互的浏览器级 e2e 验证：除了上面的 Chromium 阻塞，还需要后端预置「至少 1 张 confirmed 发票 + 1 条 submitted purchase_record（同币种、日期 ≤ 7 天、金额 ≤ 发票剩余）」夹具数据；建议下一轮在测试夹具就绪后通过 `tests/utils/privateApi.ts` 的扩展接口注入。
- ⏸️ 「可匹配发票」`listAvailableInvoices` API 类型已建模、hook 已就绪、汇总卡片已用其计数，但当前页面未直接展示「可匹配发票池子」面板（任务包未要求）；保留为后续可选扩展，类型 / 调用代码可零成本接入。
- ⏸️ 候选列表分页：当前 `listCandidates` 后端单次返回全部排序结果，前端未做分页（候选数量受 `MAX_DATE_DIFF_DAYS=7` 与币种过滤天然受限）；如未来候选 > 100 条需分页可在 `useCandidatesQuery` 与后端 `query` 上扩展，本轮无此需求。
