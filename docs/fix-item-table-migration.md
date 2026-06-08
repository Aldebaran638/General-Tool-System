# 修复 item 表 migration 问题

## 问题描述

alembic migration `681f12f91687_add_question_difficulty_and_device_type.py` 在 upgrade() 中执行了 `DROP TABLE IF EXISTS item CASCADE`，删除了 item 表。后续 migration `d19e94f5d415`（当前 head）没有重建该表。

这导致：
1. 测试数据库初始化时缺少 item 表
2. conftest.py teardown 中 `delete(Item)` 抛出异常
3. `backend/tests/items/` 下所有 item CRUD 测试失败
4. `users.py` 中删除用户时级联删除 items 的逻辑也无法执行

## 修复方案

创建新的 alembic migration（基于当前 head `d19e94f5d415`），在 upgrade() 中重建 item 表。

### item 表结构（最终版本）

基于 `681f12f91687` 的 downgrade() 中重建 item 表的定义：

```sql
CREATE TABLE item (
    description VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    id UUID NOT NULL PRIMARY KEY,
    owner_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    amount DOUBLE PRECISION,
    test_amount DOUBLE PRECISION,
    FOREIGN KEY (owner_id) REFERENCES "user"(id) ON DELETE CASCADE
);
```

注意：
- id 和 owner_id 在初始化 migration 中是 Integer，后来被 `d98dd8ec85a3` 改为 UUID
- created_at、updated_at、amount、test_amount 是后续添加的列

## 文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/app/alembic/versions/xxxx_recreate_item_table.py` | 新增 | 重建 item 表的 migration |

## 验收标准

1. `pytest backend/tests/items/` 所有测试通过
2. `pytest backend/tests/conftest.py` teardown 不再报错
3. 后端整体测试通过（111+6=117 个）
