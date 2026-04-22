架构师工作流

一. 表述规则

1. 本文件中的所有规则必须使用严格表述。
2. 本文件中禁止使用模糊表述。
3. 禁止使用以下词语：
   推荐
   可能
   可以
   尽量
   视情况
   通常
   最好
4. 所有规则必须写成可执行动作。
5. 所有步骤必须有固定顺序。
6. 所有输出物必须明确写出。
7. 所有责任边界必须明确写出。

二. 架构师在工具开发中的固定前置流程

1. 架构师在开始设计工具之前，必须先将需求转换为可落地设计。
2. 架构师在完成可落地设计之前，禁止进入数据库检查阶段。
3. 架构师在最终表字段定义明确之前，禁止进入设计文档阶段。
4. 架构师在设计文档完成之前，禁止进入测试文档阶段。
5. 架构师在设计文档完成之前，禁止进入前端页面设计阶段。
6. 架构师在设计文档完成之前，禁止进入后端接口设计阶段。

三. 第一步：将需求转换为可落地设计

执行 `skills\members\architect_skills\tool-intake.md` skill，得到 skill 输出的 json 内容。

四. 第二步：检查数据库是否支撑当前工具

执行 `skills\members\architect_skills\db-design-intake.md` skill，得到 skill 输出的 json 内容。

五. 第三步：创建设计文档

执行 `skills\members\architect_skills\api-design-doc.md` skill，得到 skill 输出的设计文档表格（HTML表格）内容。

六. 第四步：存储设计文档

执行 `skills\members\architect_skills\design-doc-storage.md` skill，将第三步产出的设计文档内容写入目标路径。

七. 第五步：创建测试文档

执行 `skills\members\architect_skills\test-doc-design.md` skill，得到 skill 输出的测试文档内容。

八. 第六步：存储测试文档

执行 `skills\members\architect_skills\test-doc-storage.md` skill，将第五步产出的测试文档内容写入目标路径。

九. 第七步：创建任务清单

执行 `skills\members\architect_skills\task-list-design.md` skill，得到 skill 输出的任务清单内容。

十. 第八步：存储任务清单

执行 `skills\members\architect_skills\task-list-storage.md` skill，将第七步产出的任务清单内容写入目标路径。

十一. 后端AI分层执行链规则

1. 架构师向后端AI发派单工具后端任务时，必须同时提供以下输入物路径：
   设计文档路径
   测试文档路径
   任务清单路径
   目标模块路径
   允许修改文件范围
   禁止修改文件范围
2. 架构师向后端AI发派单工具后端任务时，必须明确写出该任务属于单工具模块任务。
3. 后端AI接收单工具模块任务后，必须先执行 `skills/members/后端skill.md` 。
4. 后端AI执行 `skills/members/后端skill.md` 后，必须进入 `skills/tool-module-builder/SKILL.md` 执行单模块实现。
5. 架构师禁止要求后端AI绕过 `skills/members/后端skill.md` 直接执行单模块编码。
6. 架构师禁止要求后端AI在单工具模块任务中同时实现多个工具。
7. 架构师禁止要求后端AI在单工具模块任务中处理任务清单之外的无关模块。
8. 架构师生成任务清单时，必须确保任务项只覆盖目标工具模块及其直接集成改动。
9. 架构师向后端AI发派任务时，必须将任务清单作为后端AI的直接执行边界。
10. 架构师向后端AI发派任务时，必须明确写出后端AI禁止越界修改无关文件。

十二. 前端测试文件与测试AI执行规则

1. 前端AI必须负责生成本工具对应的前端测试文件。
2. 前端AI生成的前端测试文件必须与工具目录一一对应。
3. 前端AI生成的前端测试目录必须为 `frontend/tests/<group>/<tool-key>/`。
4. 前端AI生成的主测试文件必须为 `frontend/tests/<group>/<tool-key>/index.spec.ts`。
5. 前端AI允许在 `frontend/tests/<group>/<tool-key>/` 下生成辅助测试文件。
6. 架构师向前端AI发派任务时，必须明确写出前端AI负责生成本工具对应的前端测试文件。
7. 测试AI必须执行前端AI生成的前端测试文件。
8. 测试AI执行前端测试时，必须执行 `frontend/tests/<group>/<tool-key>/index.spec.ts`。
9. 测试AI禁止跳过前端AI已生成的主测试文件。
10. 测试AI执行前端测试失败后，必须输出失败测试名称、失败原因、最后一段可用日志。

十三. 后端测试文件与测试AI执行规则

1. 后端AI必须负责生成本工具对应的后端测试文件。
2. 后端AI生成的后端测试文件必须与后端模块目录一一对应。
3. 后端AI生成的后端测试目录必须为 `backend/tests/<group>/<tool-key>/`。
4. 后端AI生成的主测试文件必须为 `backend/tests/<group>/<tool-key>/index_test.py`。
5. 后端AI允许在 `backend/tests/<group>/<tool-key>/` 下生成辅助测试文件。
6. 架构师向后端AI发派任务时，必须明确写出后端AI负责生成本工具对应的后端测试文件。
7. 测试AI必须执行后端AI生成的后端测试文件。
8. 测试AI执行后端测试时，必须执行 `backend/tests/<group>/<tool-key>/index_test.py`。
9. 测试AI禁止跳过后端AI已生成的主测试文件。
10. 测试AI执行后端测试失败后，必须输出失败测试名称、失败原因、最后一段可用日志。

十四. skill 文件修改权限规则

1. `skills/members/架构师skill.md` 只允许由架构师修改。
2. `skills/members/前端skill.md` 只允许由架构师修改。
3. `skills/members/后端skill.md` 只允许由架构师修改。
4. `skills/members/测试skill.md` 只允许由架构师修改。
5. 架构师向前端AI发派任务时，禁止要求前端AI修改任何 skill 文件。
6. 架构师向后端AI发派任务时，禁止要求后端AI修改任何 skill 文件。
7. 架构师向测试AI发派任务时，禁止要求测试AI修改任何 skill 文件。
8. 前端AI接收的任务必须是前端编码任务。
9. 后端AI接收的任务必须是后端编码任务。
10. 测试AI接收的任务必须是测试执行任务或测试代码任务。
