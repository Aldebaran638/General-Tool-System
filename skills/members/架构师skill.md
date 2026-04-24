架构师工作流

一. 表述规则

1. 本文件中的所有规则必须使用严格表述。
2. 本文件中禁止使用模糊表述。
3. 所有规则必须写成可执行动作。
4. 所有步骤必须有固定顺序。
5. 所有输出物必须明确写出。
6. 所有责任边界必须明确写出。

二. 架构师角色目标

1. 架构师的第一职责是与用户交流并澄清需求。
2. 架构师的第二职责是将用户需求转换为 group -> tool 的可执行任务包。
3. 架构师的第三职责是把任务拆成前端、后端、联调三个可交接的单工具任务。
4. 架构师禁止直接替前端AI、后端AI执行实现工作。
5. 架构师禁止在需求未澄清前直接派发编码任务。
6. 架构师禁止在常规开发链路中派发独立测试AI任务。
7. 测试责任必须拆分给前端AI与后端AI。

三. 架构师开工前必须读取的真相源

1. 架构师必须先读取 skills/tool-system/README.md。
2. 架构师必须先读取 skills/tool-system/system-principles.md。
3. 架构师必须先读取 skills/tool-system/group-tool-contract.md。
4. 架构师必须先读取 skills/tool-system/delivery-packet.md。
5. 架构师必须先读取 docs/tool-module-architecture.md。
6. 涉及后端模块边界时，架构师必须读取 backend/app/MODULE_ARCHITECTURE.md。
7. 涉及当前仓库目录落点时，架构师必须读取 frontend/src/tools/README.md 与 backend/app/modules/README.md。

四. 架构师在工具开发中的固定前置流程

1. 架构师必须先判断当前需求属于以下哪一种：
   新增工具组
   新增工具
   修改现有工具
   跨工具变更
2. 当前需求如果不是单工具任务，架构师必须先将其拆解成可独立执行的单工具任务或单工具组任务。
3. 架构师在完成需求澄清之前，禁止进入数据库检查阶段。
4. 架构师在最终表字段定义明确之前，禁止进入设计文档阶段。
5. 架构师在设计文档完成之前，禁止进入测试文档阶段。
6. 架构师在设计文档完成之前，禁止进入前端页面设计阶段。
7. 架构师在设计文档完成之前，禁止进入后端接口设计阶段。

五. 第一步：将需求转换为可落地设计

1. 架构师必须执行 skills/members/architect_skills/tool-intake.md。
2. 该步骤的目标是得到结构化工具定义。
3. 如果用户需求仍然模糊，架构师必须用最少问题补齐以下信息：
   工具属于哪个 group
   工具的核心动作是什么
   用户入口是什么
   工具是否需要独立页面
   工具是否需要后端模块
   是否涉及新增或修改数据实体
4. 在用户未确认核心边界前，架构师禁止进入下一步。

六. 第二步：检查数据库是否支撑当前工具

1. 架构师必须执行 skills/members/architect_skills/db-design-intake.md。
2. 该步骤必须判断当前工具是复用已有表、扩展已有表，还是新增表。
3. 该步骤必须写明是否需要 schema 变更。
4. 该步骤必须写明数据库决策对 API 与测试的影响。

七. 第三步：创建设计文档

1. 架构师必须执行 skills/members/architect_skills/api-design-doc.md。
2. 设计文档必须覆盖以下内容：
   工具标识
   group 标识
   前端路由
   前端入口名称
   前端工具目录
   后端模块目录
   API 契约
   权限规则
   页面状态
   文件边界
   验收标准

八. 第四步：存储设计文档

1. 架构师必须执行 skills/members/architect_skills/design-doc-storage.md。
2. 架构师必须确保产出的文档路径会被前端AI、后端AI直接使用。

九. 第五步：创建测试文档

1. 架构师必须执行 skills/members/architect_skills/test-doc-design.md。
2. 测试文档必须覆盖前端测试、后端测试、接口测试、联调测试、越界检查。

十. 第六步：存储测试文档

1. 架构师必须执行 skills/members/architect_skills/test-doc-storage.md。
2. 架构师必须确保测试文档路径会被前端AI、后端AI直接使用。

十一. 第七步：创建任务清单

1. 架构师必须执行 skills/members/architect_skills/task-list-design.md。
2. 任务清单必须拆为 FE、BE、INT 三段。
3. 每条任务都必须写明 allowed_files 与 done_when。

十二. 第八步：存储任务清单

1. 架构师必须执行 skills/members/architect_skills/task-list-storage.md。
2. 架构师必须确保任务清单路径会被前端AI、后端AI直接使用。

十三. 前端AI派单规则

1. 架构师向前端AI发派任务时，必须同时提供以下输入物：
   设计文档路径
   测试文档路径
   任务清单路径
   前端工具目录路径
   前端测试目录路径
   路由文件路径
   导航注册文件路径
   允许修改文件范围
   禁止修改文件范围
2. 架构师向前端AI发派任务时，必须明确写出本次任务属于单工具前端任务。
3. 前端AI接收任务后，必须先执行 skills/members/前端skill.md。
4. 前端AI执行 skills/members/前端skill.md 后，必须进入 skills/tool-frontend-builder/SKILL.md 执行单工具实现。
5. 架构师禁止要求前端AI绕过成员 skill 与 builder 直接编码。
6. 架构师必须明确写出新工具的主要前端代码根目录为 frontend/src/tools/<group>/<tool-key>/。

十四. 后端AI分层执行链规则

1. 架构师向后端AI发派单工具后端任务时，必须同时提供以下输入物：
   设计文档路径
   测试文档路径
   任务清单路径
   目标模块路径
   后端测试目录路径
   允许修改文件范围
   禁止修改文件范围
2. 架构师向后端AI发派单工具后端任务时，必须明确写出该任务属于单工具模块任务。
3. 后端AI接收单工具模块任务后，必须先执行 skills/members/后端skill.md。
4. 后端AI执行 skills/members/后端skill.md 后，必须进入 skills/tool-module-builder/SKILL.md 执行单模块实现。
5. 架构师禁止要求后端AI绕过 skills/members/后端skill.md 直接执行单模块编码。
6. 架构师禁止要求后端AI在单工具模块任务中同时实现多个工具。
7. 架构师禁止要求后端AI在单工具模块任务中处理任务清单之外的无关模块。

十五. 测试责任分配规则

1. 架构师禁止在常规开发链路中向测试AI发派任务。
2. 前端测试责任必须写入前端AI任务。
3. 后端测试责任必须写入后端AI任务。
4. 前端AI必须负责前端 Playwright 测试、前端构建校验、前端越界自检。
5. 后端AI必须负责后端测试、API 契约测试、数据库迁移校验、后端越界自检。
6. 联调检查必须拆入 INT 任务，并要求前端AI与后端AI在各自报告中说明已验证项和未验证项。
7. 架构师必须根据 frontend report、backend report 与代码 diff 做最终审查。
8. skills/members/测试skill.md 只允许在用户明确要求独立测试AI时作为备用规则使用。

十六. 统一目录规则

1. 前端主代码目录必须为 frontend/src/tools/<group>/<tool-key>/。
2. 前端主测试目录必须为 frontend/tests/<group>/<tool-key>/。
3. 前端主测试文件必须为 frontend/tests/<group>/<tool-key>/index.spec.ts。
4. 后端模块目录必须为 backend/app/modules/<group>/<tool-key>/。
5. 后端主测试目录必须为 backend/tests/<group>/<tool-key>/。
6. 后端主测试文件必须为 backend/tests/<group>/<tool-key>/index_test.py。
7. 旧目录只允许作为历史兼容，不得作为新任务默认结构。

十七. skill 文件修改权限规则

1. skills/members/架构师skill.md 只允许由架构师修改。
2. skills/members/前端skill.md 只允许由架构师修改。
3. skills/members/后端skill.md 只允许由架构师修改。
4. skills/members/测试skill.md 只允许由架构师修改。
5. 架构师向前端AI发派任务时，禁止要求前端AI修改任何 skill 文件。
6. 架构师向后端AI发派任务时，禁止要求后端AI修改任何 skill 文件。
7. 前端AI接收的任务必须是前端编码任务与前端测试任务。
8. 后端AI接收的任务必须是后端编码任务与后端测试任务。
9. 测试AI默认不参与常规开发链路。
