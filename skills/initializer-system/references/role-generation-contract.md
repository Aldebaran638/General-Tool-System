# Role Generation Contract

初始化者不得预设“所有项目都只有前端、后端、测试”。

角色清单必须来源于仓库事实。

## 1. 固定角色

以下角色固定存在：

1. `architect`

它负责：

1. 与用户对话
2. 拆解需求
3. 生成设计、测试、任务、派单包
4. 复核执行结果

## 2. 可推导执行角色

初始化者需要根据仓库是否存在独立交付面，推导执行角色。

常见类型：

1. `frontend_tool_worker`
2. `backend_tool_worker`
3. `mobile_tool_worker`
4. `data_pipeline_worker`
5. `infra_worker`
6. `test_worker`

## 3. 推导标准

只有同时满足以下条件，某执行角色才应被创建：

1. 仓库中确实存在对应代码面。
2. 该代码面可以由独立上下文单独执行。
3. 该代码面有明确的文件边界。
4. 该代码面需要自己的验证命令或报告。

## 4. Builder 角色

当某执行角色的任务天然收敛为“单工具实现”时，应再给它配一个 builder skill。

例子：

1. `frontend_tool_worker` -> `tool-frontend-builder`
2. `backend_tool_worker` -> `tool-module-builder`

如果项目没有“单工具 builder”的必要，则 `builder_skill_path` 允许为空。

## 5. 角色命名建议

建议角色标识稳定、可预测：

1. `architect`
2. `<surface>_tool_worker`
3. `<surface>_reviewer`
4. `<surface>_builder`

## 6. 每个角色都必须明确

1. owns 什么类型的任务
2. reads 什么输入物
3. writes 什么路径
4. cannot touch 什么路径
5. 需要输出什么报告
6. 需要跑什么验证

## 7. 当前仓库的映射示例

当前仓库的合理角色为：

1. `architect`
2. `frontend_tool_worker`
3. `backend_tool_worker`
4. `test_worker`

原因是：

1. 存在独立前端代码面与测试面
2. 存在独立后端代码面与测试面
3. 架构师与执行者职责已明确分离
