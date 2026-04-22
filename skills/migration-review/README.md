# Migration Review

这份说明只管一件事：后端数据库模型变更后，如何正确生成、审查并应用数据库迁移。

## Alembic 是做什么的

Alembic 是数据库迁移工具。

它不负责业务接口，也不负责页面逻辑。它负责的是：

- 记录数据库结构版本
- 根据模型变化生成迁移脚本
- 把数据库从旧版本升级到新版本

在这个项目里，你可以把职责理解成：

- `SQLModel/SQLAlchemy` 负责定义“模型现在长什么样”
- `Alembic` 负责把数据库真正改成这个样子

## Alembic 以什么为准

Alembic 不是扫描整个 `backend/app/` 目录来找模型。

它真正参考的是：

- [backend/app/alembic/env.py](../../backend/app/alembic/env.py)

这里的关键代码是：

```python
from app.models import SQLModel
target_metadata = SQLModel.metadata
```

这表示：

- Alembic 只会根据 `target_metadata` 里已经注册进去的模型生成迁移
- 当前项目里，`target_metadata` 来自 `SQLModel.metadata`
- 哪些模型被导入并注册进 `SQLModel.metadata`，Alembic 才能看到

所以判断标准不是“模型文件放在哪”，而是：

- 这个模型是否已经接入 Alembic 可识别的模型导入链路

## 当前项目的模型导入链路

当前项目里，Alembic 的模型可见性主要依赖：

- [backend/app/models.py](../../backend/app/models.py)

因为 `env.py` 会先导入 `app.models`，再读取其中的 `SQLModel.metadata`。

这意味着：

- 只写了新模型文件，不等于 Alembic 能看到它
- 新模型必须被导入到这条链路里，才能进入 `target_metadata`

例如：

```python
from app.modules.purchase_records.purchase_record_summary.models import PurchaseRecord
```

这类导入的作用不是给业务代码用，而是为了让 `PurchaseRecord` 注册进 `SQLModel.metadata`，让 Alembic 能识别它。

## backend/app/alembic 是如何发挥作用的

`backend/app/alembic/` 这个目录不是业务代码主动 import 来执行的。

它是被 `alembic` 命令行工具加载的。

调用链路是：

1. 执行 `alembic` 命令，例如：

```bash
alembic revision --autogenerate -m "add purchase_record"
alembic upgrade head
```

2. Alembic 读取配置文件：

- [backend/alembic.ini](../../backend/alembic.ini)

3. `alembic.ini` 里指定：

```ini
script_location = app/alembic
```

4. Alembic 进入：

- [backend/app/alembic/](../../backend/app/alembic)

并加载其中的：

- `env.py`
- `versions/`
- `script.py.mako`

所以 `backend/app/alembic/` 可以理解成：

- 这是给 `alembic` 命令使用的迁移运行目录
- 不是给业务接口直接调用的目录

## env.py 里的 offline / online 是什么

- `run_migrations_offline()`：不真正连接数据库，生成离线 SQL
- `run_migrations_online()`：真正连接数据库并执行迁移

平时最常用的：

```bash
alembic upgrade head
```

实际通常走的是 `run_migrations_online()`。

## 改哪里

后端表结构变更通常涉及：

- 模型定义文件，例如模块内的 `models.py`
- 模型注册链路文件，例如 [backend/app/models.py](../../backend/app/models.py)
- 迁移文件目录：
  - [backend/app/alembic/versions/](../../backend/app/alembic/versions)

## 基本流程

1. 修改数据库模型
2. 确保新模型已经接入 Alembic 可识别的模型导入链路
3. 执行迁移审查脚本
4. 检查新生成的 migration 文件
5. 确认无误后执行数据库升级

## 你要检查什么

重点检查新 migration 文件里的：

- `upgrade()`
- `downgrade()`

至少确认这些点：

- 改的是不是你要改的表
- 新增/删除的是不是你要改的字段
- 有没有多余操作
- 外键、索引、约束是否合理
- downgrade 是否合理

## 原则

- migration 文件必须在本地项目目录生成
- migration 文件必须和代码一起提交到 Git
- 不要只在容器里生成正式 migration 文件而不落地到仓库
- 不要只写模型不写 migration
- 不要依赖测试里的 `create_all()` 临时建表掩盖 migration 缺失

## 脚本

可使用：

- [skills/migration-review/review_migration.py](./review_migration.py)

运行时需要提供一个 `message` 参数。

它会被传给：

```bash
alembic revision --autogenerate -m "..."
```

例如：

```powershell
uv run --project backend python .\skills\migration-review\review_migration.py "add purchase_record table"
```

建议：

- 迁移说明尽量使用简短英文或拼音短语
- 不要写得过长
- 最好直接说明“改了哪张表、加了什么字段”

不太推荐：

- `update`
- `修改数据库`

更推荐：

- `add test_amount to item`
- `create invoice table`
- `add purchase_record table`

## 这个脚本会做什么

它会：

- 检查数据库当前 revision 是否和本地迁移链匹配
- 检查数据库是否已经在最新 `head`
- 自动执行 `alembic revision --autogenerate`
- 找出新生成的 migration 文件
- 打印 migration 内容给你审查
- 等待你输入 `Y/N`
- 输入 `Y` 后执行 `alembic upgrade head`
- 如果生成后流程失败，会删除本次新生成的 migration 文件，避免留下半成品

## 这个脚本不能替你做什么

它不会自动修复这些问题：

- 新模型没有接入 Alembic 可识别的模型导入链路
- 迁移虽然能生成，但内容不正确
- 当前数据库状态已经异常
- 当前数据库还没先升级到最新 revision

所以它的正确定位是：

- 迁移生成 + 审查 + 应用工具

而不是：

- 无条件一键修复数据库问题的工具

## 使用前提

执行这个脚本前，必须满足：

- `uv` 已安装
- `backend` 环境可用
- 新模型已经进入 `target_metadata`
- 当前数据库如果落后于 `head`，先执行：

```bash
uv run --project backend alembic upgrade head
```

## 一句话总结

在这个项目里：

- Alembic 以 [backend/app/alembic/env.py](../../backend/app/alembic/env.py) 中的 `target_metadata` 为模型标准
- `backend/app/alembic/` 是给 `alembic` 命令使用的迁移运行目录
- `review_migration.py` 能帮你完成“生成、审查、应用 migration”，但前提是模型已经接入 Alembic 可识别链路
