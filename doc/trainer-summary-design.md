# 培训讲师汇总功能设计文档

## 1. 功能概述

新增「培训讲师汇总」页面，以表格形式展示所有培训讲师及其关联的考试信息。

同时移除工作台下的「项目管理」导航入口。

## 2. 需求详情

### 2.1 培训讲师汇总页面

- **入口位置**: 工作台分组下的独立侧边栏菜单项
- **权限**: 仅管理员（is_superuser）可见
- **展示内容**（表格列）:
  - 讲师（姓名）
  - 中心（center_snapshot，取该考试参与人员的中心信息，有多个时取第一个非空值）
  - 课程名称（考试名称）
  - 考试时间（考试开始时间）
  - 培训人数（该考试的参与人数）
- **交互**: 点击课程名称可跳转至考试详情页 `/exams/{exam_id}`

### 2.2 移除项目管理

- 从 `tool-navigation.tsx` 中移除 `project_management` 的 import 和注册
- 保留 `items.tsx` 路由文件（避免破坏现有 TanStack Router 路由树）

## 3. 后端 API 设计

### 3.1 新增 Endpoint

```
GET /api/v1/exams/admin/trainers/summary
```

**权限**: RequireExamAdmin

**Response Schema**:

```python
class TrainerSummaryItem(BaseModel):
    trainer_id: str
    trainer_name: str
    exam_id: uuid.UUID
    exam_name: str
    center: str | None    # 从 exam_participant.center_snapshot 聚合
    start_at: datetime
    participant_count: int

class TrainerSummaryResponse(BaseModel):
    data: list[TrainerSummaryItem]
    count: int
```

### 3.2 实现逻辑

1. 查询所有 `status in ("PUBLISHED", "ARCHIVED")` 且 `trainer_ids is not null` 的考试
2. 对每个考试的 `trainer_ids` 展开，为每个讲师生成一条记录
3. 关联用户表获取讲师姓名
4. 关联 `exam_participant` 统计参与人数
5. 从 `exam_participant.center_snapshot` 中取第一个非空的中心值
6. 按考试时间倒序排列

## 4. 前端设计

### 4.1 新增模块

路径: `frontend/src/tools/workbench/trainer_summary/`

文件结构:
```
trainer_summary/
├── api.ts              # API 调用
├── components/
│   └── TrainerSummaryPage.tsx   # 页面组件
└── index.ts            # 模块注册
```

### 4.2 路由

新增路由文件: `frontend/src/routes/_layout/trainer-summary.tsx`
路径: `/trainer-summary`

### 4.3 导航注册

在 `tool-navigation.tsx` 中导入并注册 `trainer_summary` 模块。

### 4.4 页面设计

- 页面标题: "培训讲师汇总"
- 表格列:
  | 列名 | 说明 |
  |------|------|
  | 讲师 | 讲师姓名 |
  | 中心 | 考试所属中心 |
  | 课程名称 | 可点击跳转考试详情 |
  | 考试时间 | 格式化为中文日期时间 |
  | 培训人数 | 该考试参与人数 |

## 5. 移除项目管理

### 5.1 修改文件

**`frontend/src/config/tool-navigation.tsx`**:
- 移除 `import "@/tools/workbench/project_management"`

### 5.2 保留文件

- `frontend/src/routes/_layout/items.tsx` — 保留以避免路由树破坏
- `frontend/src/tools/workbench/project_management/` — 保留代码文件

## 6. 任务分解

### 后端任务
1. 在 `schemas.py` 中新增 `TrainerSummaryItem` 和 `TrainerSummaryResponse`
2. 在 `service.py` 中新增 `get_trainer_summary()` 函数
3. 在 `router.py` 中新增 `/admin/trainers/summary` endpoint

### 前端任务
1. 创建 `trainer_summary/api.ts` — API 封装
2. 创建 `trainer_summary/components/TrainerSummaryPage.tsx` — 页面组件
3. 创建 `trainer_summary/index.ts` — 模块注册
4. 创建 `routes/_layout/trainer-summary.tsx` — 路由文件
5. 修改 `tool-navigation.tsx` — 注册新模块，移除项目管理

### 测试任务
1. 运行后端测试确保无回归
2. 启动前端进行 Playwright 验收测试
