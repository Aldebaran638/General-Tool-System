# Round 008 Tasks - reimbursement_excel

## BE

- 创建 `backend/app/modules/finance/reimbursement_exports/`。
- 新增 `app_setting` SQLModel 模型或平台配置模型。
- 新增 `reimbursement_export` SQLModel 模型。
- 新增 `reimbursement_export_item` SQLModel 模型。
- 新增 Alembic migration。
- 实现模板 Excel 生成 `excel_builder.py`。
- 实现文件存储 `storage.py`。
- 实现 records / generate / history / detail / download / settings / purge API。
- 实现管理员权限。
- 实现导出条件校验。
- 实现单据编号生成和快照保存。
- 实现过期文件清理。
- 新增后端测试。
- 输出 `docs/rounds/round-008/backend-report.md`。

## FE

- 创建 `frontend/src/tools/finance/reimbursement_exports/`。
- 注册财务工具组入口。
- 新增 `/finance/reimbursement-exports` 路由。
- 实现购买记录筛选。
- 实现手动勾选表格。
- 实现已导出警告。
- 实现生成配置弹窗。
- 实现导出历史表。
- 实现设置弹窗。
- 接入下载。
- 接入 i18n，或记录 Round 003 未合并阻塞。
- 新增前端测试。
- 输出 `docs/rounds/round-008/frontend-report.md`。

## INT

- 确认管理员生成 Excel。
- 确认普通用户无权。
- 确认 Excel 模板格式保留。
- 确认单据编号按类别顺序。
- 确认导出历史可追踪。
- 确认过期文件清理只删文件不删历史。
