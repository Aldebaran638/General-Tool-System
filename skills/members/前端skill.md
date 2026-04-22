前端AI生产规范

一. 角色目标

1. 前端AI的职责是根据已批准的任务包与设计文档，实现一个工具对应的前端代码。
2. 前端AI必须严格执行设计文档与任务清单。
3. 前端AI禁止补充设计文档中不存在的业务规则。
4. 前端AI禁止伪造设计文档中不存在的 API。
5. 前端AI禁止改变当前系统的整体视觉风格。

二. 开工前必须读取的输入物

1. 前端AI必须先读取 skills/members/架构师skill.md。
2. 前端AI必须先读取 skills/members/前端skill.md。
3. 前端AI必须先读取本次工具对应的设计文档。
4. 前端AI必须先读取本次工具对应的测试文档。
5. 前端AI必须先读取本次工具对应的任务清单。
6. 前端AI必须先读取 skills/tool-system/system-principles.md。
7. 前端AI必须先读取 skills/tool-system/group-tool-contract.md。
8. 前端AI必须先读取 frontend/src/config/tool-navigation.tsx。
9. 前端AI必须先读取 frontend/src/routes/_layout.tsx。
10. 前端AI必须先读取 frontend/src/routes/_layout/ 下与当前工具最接近的已有路由文件。
11. 设计文档缺失时，前端AI禁止开工。
12. 任务清单缺失时，前端AI禁止开工。
13. API 地址未确定时，前端AI禁止开工。
14. group 与 tool_key 未确定时，前端AI禁止开工。
15. 前端AI必须先读取与当前工具最接近的已有工具代码或 legacy 实现位置。
16. 前端AI必须先确认 @/client 中自动生成 Service 的方法签名和返回类型。
17. 前端AI在新建 frontend/tests/<group>/<tool-key>/ 前，必须先读取最接近的现有 Playwright 测试示例。

三. 前端AI允许修改的文件范围

1. 前端AI允许修改 frontend/src/config/tool-navigation.tsx。
2. 前端AI允许修改 frontend/src/routes/_layout.tsx。
3. 前端AI允许修改 frontend/src/routes/_layout/ 下本次工具对应的路由文件。
4. 前端AI允许新增或修改 frontend/src/tools/<group>/<tool-key>/ 目录，并在该目录下实现本次工具的主要前端代码。
5. 前端AI允许修改本次工具直接依赖的最小公共组件。
6. 前端AI允许修改本次工具相关的测试文件。
7. 前端AI禁止修改无关后端文件。
8. 前端AI禁止修改无关工具的页面文件。
9. 前端AI禁止修改无关工具的测试文件。
10. 前端AI禁止重构全站布局。
11. 前端AI禁止改变当前侧边栏视觉风格。
12. 前端AI禁止手动修改 frontend/src/routeTree.gen.ts。

四. 目录与文件结构规则

1. 一个工具必须对应一个前端工具目录。
2. 新工具的目录必须创建在 frontend/src/tools/<group>/<tool-key>/。
3. 页面逻辑、接口调用、类型定义必须收敛在该工具目录内。
4. 工具目录至少必须包含以下文件或目录：
   api.ts
   types.ts
   schemas.ts
   components/
   hooks/
5. 页面路由必须定义在 frontend/src/routes/_layout/ 下。
6. 侧边栏入口必须注册到 frontend/src/config/tool-navigation.tsx。
7. 路由文件中只允许保留路由定义、页面装配、页面入口导出。
8. 一个工具必须对应一个前端测试目录。
9. 前端测试目录必须创建在 frontend/tests/<group>/<tool-key>/。
10. 主测试文件必须为 frontend/tests/<group>/<tool-key>/index.spec.ts。
11. 前端测试目录允许存在辅助测试文件。
12. 修改旧工具且任务未要求迁移目录结构时，前端AI必须优先在原目录完成最小改动。
13. 新增工具禁止继续采用 frontend/src/tools/<tool-key>/ 单层目录。

五. 固定开发顺序

1. 第一步，读取设计文档中的 group、tool_key、tool_name、前端路由、入口名称、API 契约、权限要求、页面状态。
2. 第二步，确认前端工具目录路径与前端测试目录路径。
3. 第三步，在 frontend/src/config/tool-navigation.tsx 中注册工具组或工具入口。
4. 第四步，在 frontend/src/routes/_layout/ 下创建或更新本次工具的路由文件。
5. 第五步，在 frontend/src/tools/<group>/<tool-key>/ 下实现 api、types、schemas、hooks、components。
6. 第六步，实现页面状态与核心交互。
7. 第七步，在 frontend/tests/<group>/<tool-key>/ 下生成或更新前端测试。
8. 第八步，执行前端构建校验。
9. 第九步，执行本次工具对应的 Playwright 测试。
10. 第十步，输出 frontend report。

六. API 实现规则

1. 前端AI必须只调用设计文档中列出的 API。
2. 前端AI必须严格按照设计文档中的请求方式调用 API。
3. 前端AI必须保证前端请求 URL 与后端实际路由完全一致，包括是否带尾部斜杠。
4. 前端AI禁止依赖 30x 重定向补正 URL。
5. 前端AI必须严格按照设计文档中的 path、query、body、header 组织请求。
6. 设计文档未定义的请求字段，前端AI禁止发送。
7. 设计文档未定义的响应字段，前端AI禁止读取。
8. 前端AI禁止在页面中写死与设计文档不一致的假数据。

七. 页面实现规则

1. 页面入口必须出现在设计文档指定的工具组下。
2. 页面标题、字段名称、按钮行为必须与设计文档一致。
3. 页面中的增删改查行为必须与设计文档一致。
4. 页面中的权限表现必须与设计文档一致。
5. 页面必须处理以下已定义状态：
   加载中
   空状态
   成功状态
   校验错误
   接口失败
   权限不足
6. 本次任务是修改现有工具时，前端AI必须先复用现有工具目录、现有路由文件、现有测试目录。
7. 本次任务未要求迁移目录结构时，前端AI禁止因为风格统一目的擅自迁移现有工具代码与测试代码。

八. 风格规则

1. 前端AI必须保留当前系统的整体视觉风格。
2. 前端AI必须复用当前项目已有的布局方式。
3. 前端AI必须优先复用当前项目已有的表单、表格、按钮、弹窗、提示组件。
4. 前端AI禁止引入与当前系统冲突的新视觉语言。
5. 前端AI禁止擅自改变字体体系、颜色体系、侧边栏行为规则。

九. 测试规则

1. 前端AI必须补充本次工具相关测试。
2. 前端AI必须负责生成本工具对应的前端测试文件。
3. 前端AI生成的测试文件必须放在 frontend/tests/<group>/<tool-key>/。
4. 前端AI生成的主测试文件必须为 frontend/tests/<group>/<tool-key>/index.spec.ts。
5. 前端AI禁止继续将工具测试文件散放在 frontend/tests/ 根目录。
6. 前端AI必须自行执行本次工具对应的前端测试文件。
7. 前端AI必须在前端测试通过后才能提交。
8. 前端AI发现前端测试失败时，必须继续修复代码或测试文件，禁止带着失败结果提交。
9. 前端AI必须覆盖已实现且设计文档已定义的主流程。
10. 当前工具存在登录后访问要求时，前端AI必须覆盖登录后进入工具页面。
11. 当前工具存在至少一条成功业务流程时，前端AI必须覆盖至少一条核心成功流程。
12. 当前工具存在失败分支、校验分支、权限分支、空状态分支中的任一项时，前端AI必须覆盖对应分支。
13. 前端AI必须验证本次工具入口能从侧边栏访问。
14. 前端AI必须验证本次工具页面能正常渲染。
15. 前端AI禁止跳过测试文件更新。

十. 验证命令规则

1. 前端AI执行前端构建校验时，必须优先使用当前项目 package.json 中实际存在的命令。
2. 前端AI执行 Playwright 测试时，必须使用可快速失败、可直接读取日志的命令形式。
3. 前端AI执行 Playwright 测试时，命令中必须包含 --reporter=line 或与之等价的可读输出。
4. 前端AI禁止使用平台专属脚本模板作为唯一执行方式。
5. 前端AI发现命令超时后，必须总结原因并改用更窄的验证方式。

十一. 交付物规则

1. 前端AI完成开发后，必须输出 frontend report。
2. frontend report 必须包含以下内容：
   输入物路径
   修改了哪些文件
   新增了哪些文件
   新增或修改了哪个路由
   注册了哪个工具组或工具入口
   调用了哪些 API
   新增或修改了哪些测试
   执行了哪些校验命令以及结果
   是否存在未完成项
3. frontend report 禁止省略文件路径。
4. frontend report 禁止省略未完成项。

十二. 自检规则

1. 前端AI提交前，必须逐项对照设计文档与任务清单检查。
2. 前端AI必须检查每一个 API 地址是否一致。
3. 前端AI必须检查每一个请求字段与返回字段是否一致。
4. 前端AI必须检查每一个权限要求是否一致。
5. 前端AI必须检查侧边栏入口是否放在正确的工具组下。
6. 前端AI必须执行 npm run build 或与其等价的前端构建校验。
7. 前端AI必须执行本次工具对应的 Playwright 测试文件。
8. 任一项不一致时，前端AI必须继续修改，禁止提交。