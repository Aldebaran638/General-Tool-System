# Round 001 Test Plan - purchase_records

## 1. 前端 AI 负责

测试路径：

- `frontend/tests/finance/purchase_records/index.spec.ts`

必须覆盖：

- 侧边栏出现“财务”工具组和“购买记录”入口。
- 从侧边栏进入 `/finance/purchase-records`。
- 空状态显示。
- 创建购买记录表单可打开。
- 上传截图后触发 OCR 预填流程。
- OCR 失败时允许手填。
- 大类不是 `other_project` 时小类必须为空。
- 大类是 `other_project` 时小类可选择。
- 保存草稿成功。
- 提交成功。
- 提交后可撤回。
- 已删除筛选可切换。
- 删除后记录进入已删除列表。
- 已删除记录可恢复。
- 管理员能看到批准、驳回、撤回批准操作。

前端校验命令：

- `docker compose exec frontend bun run build`
- `docker compose exec frontend bun run test -- tests/finance/purchase_records/index.spec.ts --reporter=line`

前端报告必须说明：

- 执行了哪些测试。
- 哪些联调项已验证。
- 哪些联调项未验证及原因。
- 是否存在越界修改。

## 2. 后端 AI 负责

测试路径：

- `backend/tests/finance/purchase_records/index_test.py`

必须覆盖：

- 普通用户创建草稿。
- 创建时保存截图元数据。
- OCR preview 不落库。
- 大类/小类校验。
- 普通用户只能查看自己的正常记录。
- 管理员可查看所有正常记录。
- `deleted=true` 只返回当前删除者删除的记录。
- `draft -> submitted`。
- `submitted -> draft`。
- `submitted -> rejected` 管理员限定。
- `rejected -> submitted`。
- `submitted -> approved` 管理员限定。
- `approved -> submitted` 管理员撤回批准。
- 普通用户不能批准、驳回、撤回批准。
- 普通用户和管理员可逻辑删除授权范围内的记录。
- 删除者可恢复。
- 非删除者不能查看或恢复已删除记录。
- 截图下载接口鉴权。
- 清理 30 天前逻辑删除记录时删除文件和数据库记录。

后端校验命令：

- `docker compose exec backend pytest backend/tests/finance/purchase_records/index_test.py`
- `docker compose exec backend alembic current`
- 如新增 migration，执行 `docker compose exec backend alembic upgrade head`

后端报告必须说明：

- 执行了哪些后端测试。
- API 契约测试结果。
- 迁移校验结果。
- 哪些联调项已验证。
- 哪些联调项未验证及原因。
- 是否存在越界修改。

## 3. 架构师最终审查

架构师根据：

- frontend report
- backend report
- git diff
- 本测试计划

检查：

- 前端和后端是否越界。
- 是否存在未执行测试。
- 前后端 API 契约是否一致。
- OCR 是否没有持久化中间结果。
- 文件是否没有保存到数据库二进制字段。
- 状态流转是否与需求一致。
