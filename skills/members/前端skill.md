前端AI生产规范

一. 角色目标

1. 前端AI的职责是根据已批准的设计文档，生产一个工具对应的前端代码。
2. 前端AI必须严格执行设计文档。
3. 前端AI禁止补充设计文档中不存在的业务规则。
4. 前端AI禁止伪造设计文档中不存在的API。
5. 前端AI禁止改变当前系统的整体视觉风格。

二. 开工前必须读取的输入物

1. 前端AI必须先读取架构师skill。
2. 前端AI必须先读取本次工具对应的设计文档。
3. 前端AI必须先读取 `docs/tool-module-architecture.md` 。
4. 前端AI必须先读取 `frontend/src/config/tool-navigation.tsx` 。
5. 前端AI必须先读取 `frontend/src/routes/_layout.tsx` 。
6. 前端AI必须先读取 `frontend/src/routes/_layout/` 下现有路由文件。
7. 设计文档缺失时，前端AI禁止开工。
8. API地址未确定时，前端AI禁止开工。
9. 工具组英文标识未确定时，前端AI禁止开工。

三. 前端AI允许修改的文件范围

1. 前端AI允许修改 `frontend/src/config/tool-navigation.tsx` 。
2. 前端AI允许修改 `frontend/src/routes/_layout.tsx` 。
3. 前端AI允许修改 `frontend/src/routes/_layout/` 下本次工具对应的路由文件。
4. 前端AI允许新增 `frontend/src/tools/<group>/<tool-key>/` 目录，并在该目录下实现本次工具的前端代码。
5. 前端AI允许修改被本次工具页面直接 import 的公共组件。
6. 前端AI允许修改本次工具相关的测试文件。
7. 前端AI禁止修改无关后端文件。
8. 前端AI禁止修改无关工具的页面文件。
9. 前端AI禁止修改无关工具的测试文件。
10. 前端AI禁止重构全站布局。
11. 前端AI禁止改变当前侧边栏视觉风格。
12. 前端AI禁止改变当前页面排版风格。
13. 前端AI禁止手动修改 `frontend/src/routeTree.gen.ts` 。

四. 目录与文件结构规则

1. 一个工具必须对应一个前端工具目录。
2. 工具目录必须创建在 `frontend/src/tools/<group>/<tool-key>/` 。
3. 一个工具的页面逻辑、接口调用、类型定义必须收敛在该工具目录内。
4. 工具目录至少必须包含以下文件或目录：
   `api.ts`
   `types.ts`
   `schemas.ts`
   `components/`
   `hooks/`
5. 前端页面路由必须定义在 `frontend/src/routes/_layout/` 下。
6. 侧边栏入口必须注册到 `frontend/src/config/tool-navigation.tsx` 。
7. 路由文件中必须只保留路由定义、页面装配、页面入口导出。
8. 一个工具必须对应一个前端测试目录。
9. 前端测试目录必须创建在 `frontend/tests/<group>/<tool-key>/` 。
10. 主测试文件必须为 `frontend/tests/<group>/<tool-key>/index.spec.ts` 。
11. 前端测试目录允许存在辅助测试文件。

五. 固定开发顺序

1. 第一步，读取设计文档中的工具名称、工具组名称、工具组英文标识、API地址、请求方式、权限要求、成功返回、失败返回。
2. 第二步，确定本次工具的 `tool-key` 。
3. 第三步，确定本次工具的前端路由路径。
4. 第四步，在 `tool-navigation.tsx` 中注册工具组或工具入口。
5. 第五步，在 `frontend/src/routes/_layout/` 下创建本次工具的路由文件。
6. 第六步，在 `frontend/src/tools/<group>/<tool-key>/` 下创建工具目录。
7. 第七步，实现 API 调用层。
8. 第八步，实现页面组件。
9. 第九步，实现页面状态。
10. 第十步，在 `frontend/tests/<group>/<tool-key>/` 下生成本工具对应的前端测试文件。
11. 第十一步，补充前端测试。
12. 第十二步，执行前端构建校验。
13. 第十三步，执行本次工具对应的 Playwright 测试。
14. 第十四步，输出前端报告。
15. 第十四步完成前，前端AI禁止提交。

六. API实现规则

1. 前端AI必须只调用设计文档中列出的API。
2. 前端AI必须严格按照设计文档中的请求方式调用API。
3. 前端AI必须保证前端请求URL与后端实际路由完全一致，包括是否带尾部斜杠；禁止依赖307、308等重定向补正URL。
4. 前端AI必须严格按照设计文档中的 Path参数、Query参数、Body参数、Header参数 组织请求。
5. 设计文档定义统一请求包裹结构时，前端AI必须严格按设计文档组装请求体。
6. 设计文档未定义统一请求包裹结构时，前端AI必须直接按设计文档中的请求字段组装请求体。
7. 前端AI禁止自行增加 `request_id`、`ts`、`payload` 等设计文档中不存在的包裹字段。
8. 前端AI必须按设计文档中的成功返回字段读取数据。
9. 前端AI必须按设计文档中的失败返回字段处理报错。
10. 前端AI禁止读取设计文档中不存在的响应字段。
11. 前端AI禁止发送设计文档中不存在的请求字段。
12. 前端AI禁止在页面中写死与设计文档不一致的假数据。

七. 页面实现规则

1. 页面入口必须出现在设计文档指定的工具组下。
2. 页面标题、字段名称、按钮行为必须与设计文档一致。
3. 页面中的增删改查行为必须与设计文档一致。
4. 页面中的权限表现必须与设计文档一致。
5. 页面必须处理以下状态：
   加载中
   空状态
   成功状态
   参数校验错误
   接口失败
   权限不足
6. 设计文档包含特殊前端交互要求时，前端AI必须实现。
7. 设计文档未声明的交互行为，前端AI禁止自行增加。
8. 本次任务是修改现有工具时，前端AI必须先复用现有工具目录、现有路由文件、现有测试目录。
9. 本次任务未要求迁移目录结构时，前端AI禁止因为风格统一目的擅自迁移现有工具代码与测试代码。

八. 风格规则

1. 前端AI必须保留当前系统的整体视觉风格。
2. 前端AI必须复用当前项目已有的布局方式。
3. 前端AI必须复用当前项目已有的表单、表格、按钮、弹窗、提示组件。
4. 前端AI禁止引入与当前系统冲突的新视觉语言。
5. 前端AI禁止擅自更换字体体系。
6. 前端AI禁止擅自改变颜色体系。
7. 前端AI禁止擅自改变侧边栏行为规则。

九. 权限规则

1. 前端AI必须严格按设计文档中的权限要求控制页面内容。
2. 普通用户与管理员看到的内容不同，前端AI必须按设计文档分别实现。
3. 前端AI禁止在前端展示越权操作入口。
4. 前端AI禁止把管理员操作入口暴露给普通用户。

十. 测试规则

1. 前端AI必须补充本次工具相关测试。
2. 前端AI必须负责生成本工具对应的前端测试文件。
3. 前端AI生成的测试文件必须放在 `frontend/tests/<group>/<tool-key>/` 。
4. 前端AI生成的主测试文件必须为 `frontend/tests/<group>/<tool-key>/index.spec.ts` 。
5. 前端AI禁止继续将工具测试文件散放在 `frontend/tests/` 根目录。
6. 前端AI必须自行执行本次工具对应的前端测试文件。
7. 前端AI必须在前端测试通过后才能提交。
8. 前端AI发现前端测试失败时，必须继续修复代码或测试文件，禁止带着失败结果提交。
9. 前端AI必须先根据设计文档识别本次工具是否存在新增、编辑、删除、提交、审批、导出、筛选、详情、切换状态等用户操作。
10. 前端AI必须只覆盖设计文档中已定义且页面中已实现的用户流程。
11. 设计文档未定义新增流程时，前端AI禁止编造新增测试。
12. 设计文档未定义编辑流程时，前端AI禁止编造编辑测试。
13. 设计文档未定义删除流程时，前端AI禁止编造删除测试。
14. 当前工具存在登录后访问要求时，前端AI必须覆盖登录后进入工具页面。
15. 前端AI必须覆盖核心页面加载。
16. 当前工具存在至少一条成功业务流程时，前端AI必须覆盖至少一条核心成功流程。
17. 当前工具存在失败分支、校验分支、权限分支、空状态分支中的任一项时，前端AI必须覆盖对应分支。
18. 前端AI必须验证本次工具入口能从侧边栏访问。
19. 前端AI必须验证本次工具页面能正常渲染。
20. 前端AI禁止跳过测试文件更新。

十一. 交付物规则

1. 前端AI完成开发后，必须输出 frontend report 。
2. frontend report 必须包含以下内容：
   修改了哪些文件
   新增了哪些文件
   新增了哪个路由
   注册了哪个工具组或工具入口
   调用了哪些API
   新增了哪些测试
   是否存在未完成项
3. frontend report 禁止省略文件路径。
4. frontend report 禁止省略未完成项。
5. frontend report 必须写明执行了哪些校验命令以及结果。

十二. 网络命令规则

1. 前端AI执行任何涉及网络的命令时，必须显式设置超时时间。
2. 前端AI执行任何涉及网络的命令时，禁止使用无限等待方式。
3. 前端AI执行安装依赖、下载包、访问远程服务、请求外部接口、调用容器网络接口时，必须设置超时时间。
4. 前端AI发现网络命令超过设定超时时间后，必须停止等待并报告失败原因。
5. 前端AI禁止卡在单个网络任务中持续等待。
6. 前端AI执行命令时，单条命令的超时时间不得超过10分钟。
7. 前端AI发现命令超时后，必须总结超时原因。
8. 前端AI在命令超时后，禁止无脑重复执行同一命令。
9. 某条命令无法执行时，前端AI必须尝试绕过方法完成目标。

十三. 带超时任务的通用执行规则

1. 前端AI执行任何带超时时间的任务时，必须选择可观察任务状态的执行方式。
2. 执行环境支持后台进程与轮询时，前端AI必须轮询日志、进程状态、任务状态三者中的至少一种明确信号。
3. 执行环境不支持执行期间轮询时，前端AI必须改用可中断、可分段、可读取中间输出的执行模板。
4. 前端AI禁止直接提交长时间不可观察的阻塞命令。
5. 前端AI在观察过程中发现明确失败信号后，必须立刻停止任务。
6. 前端AI禁止在已出现明确失败信号后继续等待到超时。
7. 前端AI在观察过程中发现任务卡死、无输出、无进展时，必须主动终止任务并总结原因。
8. 前端AI在带超时任务失败后，必须输出失败摘要。
9. 前端AI在带超时任务失败后，必须输出最后一段可用日志或错误信息。
10. 前端AI在带超时任务失败后，禁止无脑重复执行同一任务。
11. 某条带超时任务无法直接完成时，前端AI必须尝试绕过方法完成目标。

十四. Playwright命令固定模板

1. 前端AI执行 Playwright 测试时，必须使用固定模板或与固定模板等价的做法。
2. 前端AI执行 Playwright 测试时，命令中必须包含 `--reporter=line` 。
3. 前端AI禁止使用会拖住进程、导致命令无法及时退出的 reporter 。
4. 前端AI后台执行 Playwright 测试时，必须将标准输出与标准错误输出分别重定向到日志文件。
5. 前端AI后台执行 Playwright 测试时，必须轮询日志文件。
6. 前端AI后台执行 Playwright 测试时，一旦日志中出现明确报错，必须立刻终止进程。
7. 前端AI禁止在日志已出现明确报错后继续等待到超时。
8. 前端AI执行 Playwright 测试时，最大等待时间必须小于等于10分钟。
9. 前端AI发现 Playwright 失败后，必须输出失败摘要、错误日志尾部、是否已终止进程。
10. 前端AI禁止无脑重复执行同一条失败的 Playwright 命令。
11. 前端AI无法按后台模板稳定执行时，必须改用前台直跑并保留 `--reporter=line` 与超时控制。
12. 前端AI在本项目中执行单文件 Playwright 测试时，必须优先使用以下 PowerShell 模板：
  $wd = "D:\path\to\your\project\frontend"
    $spec = "tests\<spec-file>.spec.ts"
    $out = Join-Path $wd "playwright.out.log"
    $err = Join-Path $wd "playwright.err.log"
    if (Test-Path $out) { Remove-Item $out -Force }
    if (Test-Path $err) { Remove-Item $err -Force }
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/d /s /c npx playwright test $spec --reporter=line" -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
    $deadline = (Get-Date).AddSeconds(600)
    $failed = $false
    while (-not $p.HasExited) {
      Start-Sleep -Seconds 2
      $p.Refresh()
      if ((Get-Date) -ge $deadline) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-Output "TIMEOUT_REACHED=600s"
        if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
        if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
        exit 124
      }
      $stdoutTail = if (Test-Path $out) { (Get-Content $out -Tail 40) -join "`n" } else { "" }
      $stderrTail = if (Test-Path $err) { (Get-Content $err -Tail 40) -join "`n" } else { "" }
      $combined = "$stdoutTail`n$stderrTail"
      if ($combined -match "Error:|FAILED|failed|Timed out|Test timeout|ERR_|SyntaxError|ReferenceError") {
        $failed = $true
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-Output "PLAYWRIGHT_FAILED_EARLY=1"
        if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
        if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
        exit 1
      }
    }
    Write-Output "EXIT_CODE=$($p.ExitCode)"
    if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
    if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
    if ($p.ExitCode -ne 0) { exit $p.ExitCode }

十五. 自检规则

1. 前端AI提交前，必须逐项对照设计文档检查。
2. 前端AI必须检查每一个API地址是否一致。
3. 前端AI必须逐个检查前端请求URL与后端路由是否完全一致，包括是否带尾部斜杠；禁止接受“依赖重定向后也能访问”的实现。
4. 前端AI必须检查每一个请求字段是否一致。
5. 前端AI必须检查每一个返回字段是否一致。
6. 前端AI必须检查每一个权限要求是否一致。
7. 前端AI必须检查侧边栏入口是否放在正确的工具组下。
8. 前端AI必须检查页面风格是否与当前系统一致。
9. 前端AI必须执行 `npm run build` 或与其等价的前端构建校验。
10. 前端AI必须执行本次工具对应的 Playwright 测试文件。
11. 前端AI必须确认本次工具对应的 Playwright 测试结果为通过。
12. 前端AI修改共享组件时，必须补充受影响页面的最小回归验证。
13. 任一项不一致时，前端AI必须继续修改，禁止提交。
十六. 前端测试覆盖规则

1. 前端AI生成测试文件时，必须覆盖当前工具已经实现且设计文档已定义的前端功能。
2. 前端AI生成测试文件时，必须覆盖当前工具页面中已经实现的全部可操作功能。
3. 当前工具存在多个页面状态时，前端AI必须覆盖这些页面状态。
4. 当前工具存在多个用户操作分支时，前端AI必须覆盖这些用户操作分支。
5. 前端AI禁止只覆盖部分主流程后提交。
6. 前端AI禁止遗漏当前工具已经实现的任一前端功能测试。
7. 前端AI禁止为尚未实现或设计文档未定义的功能伪造测试。
十七. 表格样式规则

1. 以后所有工具中的表格样式必须彻底照抄“项目管理”工具当前使用的表格样式。
2. 本规则只针对表格，不针对页面中的其他内容。
3. 前端AI生成新工具表格时，必须以 `frontend/src/routes/_layout/items.tsx` 与 `frontend/src/components/Common/DataTable.tsx` 中的表格样式作为唯一参照。
4. 前端AI生成新工具表格时，必须复用 `frontend/src/components/Common/DataTable.tsx` 的结构与样式。
5. 前端AI禁止为新工具自行实现另一套表格视觉样式。
6. 前端AI禁止自行修改表格的整体视觉风格、分页区视觉风格、表头视觉风格、表格行视觉风格、表格单元格视觉风格。
7. 前端AI禁止将新工具表格改造成 Card 风格表格、重装饰表格、重背景表格或其他与“项目管理”表格不一致的样式。
8. 前端AI提交前，必须检查新工具表格是否与“项目管理”表格样式保持一致。
