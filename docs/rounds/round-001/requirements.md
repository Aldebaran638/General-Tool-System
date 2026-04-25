# Round 001 Requirements - purchase_records

## 1. 轮次目标

本轮只实现财务工具组下的 `purchase_records` 工具。

目标是完成购买记录上传与管理：

- 用户上传购买记录截图。
- 后端使用 PaddleOCR 本地预训练模型做 OCR 预填。
- OCR 结果只返回给前端表单预填，不作为独立业务数据持久化。
- 用户确认或修改表单后提交正式购买记录。
- 系统保存购买记录正式字段与原始截图文件。
- 普通用户管理自己的记录。
- 管理员查看所有正常记录并可驳回、撤回批准。
- 普通用户和管理员都可以逻辑删除自己可操作的记录。
- 已删除记录通过列表筛选查看，可恢复，30 天后自动清空。

## 2. 工具身份

- group: `finance`
- group_name: 财务
- tool_key: `purchase_records`
- tool_name: 购买记录
- navigation_label: 购买记录
- route_path: `/finance/purchase-records`
- frontend_root: `frontend/src/tools/finance/purchase_records/`
- backend_root: `backend/app/modules/finance/purchase_records/`
- frontend_test_root: `frontend/tests/finance/purchase_records/`
- backend_test_root: `backend/tests/finance/purchase_records/`

## 3. 已确认字段

购买记录正式字段：

- purchase_date: 购买日期
- amount: 金额
- currency: 币种
- order_name: 订单名称
- category: 大类
- subcategory: 小类
- note: 备注
- screenshot file metadata: 截图文件元数据

不需要订单号字段。

## 4. 字典规则

语言：

- `zh-CN`: 简体中文
- `en-US`: 英文
- `zh-TW`: 繁体中文

币种：

- 使用 ISO 4217 三位代码。
- 第一版至少支持：`CNY`、`USD`、`EUR`、`JPY`、`HKD`、`GBP`、`AUD`、`CAD`、`SGD`。

大类使用稳定编码存储，前端三语言显示：

- `transportation`: 交通费用
- `meals_entertainment`: 膳食 / 应酬费用
- `vehicle`: 汽车费用
- `other_project`: 其他项目费用

小类使用稳定编码存储，前端三语言显示：

- `agv`: 自动导航承载车
- `painting_robot`: 智能喷漆机器人
- `rebar_robot`: 钢筋折弯与结扎机器人
- `fleet_scheduling`: 生产线车队调度
- `rd_expense`: 研发部开销

小类规则：

- 当且仅当 `category = other_project` 时，`subcategory` 允许非空。
- 当 `category != other_project` 时，`subcategory` 必须为空。

## 5. 状态规则

购买记录主状态：

- `draft`: 草稿
- `submitted`: 已提交
- `approved`: 已签字/已批准
- `rejected`: 已驳回

发票匹配状态为并行状态：

- `unmatched`: 未匹配发票
- `matched`: 已匹配发票

本轮只保存并展示匹配状态，默认 `unmatched`，不实现发票匹配工具。

状态流转：

- 创建后默认为 `draft`。
- `draft -> submitted`: 用户提交。
- `submitted -> draft`: 用户撤回提交。
- `submitted -> rejected`: 管理员驳回。
- `rejected -> submitted`: 用户修改后重新提交。
- `submitted -> approved`: 管理员批准。
- `approved -> submitted`: 管理员撤回批准。

编辑规则：

- `draft` 可编辑。
- `rejected` 可编辑。
- `submitted` 不可直接编辑，必须先撤回为 `draft`。
- `approved` 不可直接编辑，管理员可先撤回为 `submitted`。
- 已匹配发票的购买记录允许修改，本轮暂不自动打回未匹配，也不增加 `match_needs_review`。

## 6. 权限规则

普通用户：

- 创建自己的购买记录。
- 查看自己的正常记录。
- 查看自己删除的记录。
- 编辑自己的 `draft` 或 `rejected` 记录。
- 提交自己的 `draft` 或 `rejected` 记录。
- 撤回自己的 `submitted` 记录。
- 逻辑删除自己的记录。
- 恢复自己删除的记录。

管理员：

- 查看所有正常购买记录。
- 查看自己删除的记录。
- 驳回任意 `submitted` 记录。
- 批准任意 `submitted` 记录。
- 撤回任意 `approved` 记录到 `submitted`。
- 逻辑删除任意记录。
- 恢复自己删除的记录。

逻辑删除：

- 逻辑删除后的记录只有执行删除的人自己看得到。
- 逻辑删除保留 30 天。
- 超过 30 天后自动清空。
- 本轮实现清理函数与可调用接口，不要求后台定时任务。

## 7. 文件存储

- 原始截图必须保存。
- 文件存储在本地文件系统。
- 数据库不保存文件二进制。
- 数据库只保存截图文件相对路径、原始文件名、MIME 类型、文件大小。
- 推荐目录：`runtime_data/uploads/finance/purchase_records/`。
- 后端必须生成 UUID 文件名，禁止信任用户文件名作为存储文件名。
- 下载/预览截图必须走鉴权接口。

## 8. OCR 规则

- OCR 使用 PaddleOCR 本地预训练模型。
- 本地运行。
- 不训练模型。
- 不接入大模型。
- 不接入云 OCR 或第三方 AI 服务。
- 运行期不得依赖外网。
- OCR 必须受全局配置控制：
  - `ENABLE_LLM=false`
  - `ENABLE_LOCAL_OCR=true`
  - `OCR_PROVIDER=paddleocr`
  - `OCR_MODEL_DIR=runtime_data/models/paddleocr`
  - `OCR_ALLOW_MODEL_DOWNLOAD=false`
- OCR 接口只返回预填字段，不落库。
- 用户最终提交的表单字段才是正式业务数据。

## 9. 本轮不做

- 不实现 PDF 发票上传。
- 不实现发票匹配算法。
- 不实现签字专用页面。
- 不实现统计总览。
- 不实现报销单 Excel。
- 不实现独立测试 AI 派单。
