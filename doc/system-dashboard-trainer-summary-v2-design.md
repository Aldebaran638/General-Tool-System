# 系统总览 + 培训讲师汇总 V2 设计文档

## 1. 功能概述

### 1.1 系统总览改造
- 增加时间范围筛选（快捷选项 + 自定义日期）
- 移除「题库难易度占比」图表（因所有题目难度均为默认 MEDIUM，无实际意义）

### 1.2 培训讲师汇总改造
- 按讲师分组展示（每个讲师一个卡片区域）
- 每个讲师下的考试按时间倒序排列
- 添加搜索框（支持搜索讲师姓名、课程名称）
- 添加时间筛选（按考试开始时间范围筛选）

## 2. 后端 API 改造

### 2.1 系统总览

```
GET /api/v1/exams/admin/dashboard/stats?start_date=2026-01-01&end_date=2026-06-30
```

**新增 Query 参数**：
- `start_date`: string (YYYY-MM-DD, optional) — 筛选考试 start_at >= start_date
- `end_date`: string (YYYY-MM-DD, optional) — 筛选考试 start_at <= end_date (含当日结束)

**改造逻辑** (`get_system_stats`)：
- 当提供 start_date/end_date 时，所有统计只统计该时间范围内的考试及其关联数据
- exam_count: 筛选时间范围内的考试数量
- total_participation: 只统计时间范围内考试的参与人数
- overall_pass_rate: 只统计时间范围内完成考试的及格率
- question_count: 时间范围内考试的题目总数（或保持全部，视需求而定）
- paper_count: 时间范围内生成试卷的数量
- device_type_distribution: 只统计时间范围内考试提交的设备类型
- 移除 difficulty_distribution 字段

**Schema 变更**：
```python
class SystemDashboardStats(BaseModel):
    exam_count: int
    total_participation: int
    overall_pass_rate: float
    question_count: int
    paper_count: int
    question_type_distribution: list[QuestionTypeCount]
    device_type_distribution: list[DeviceTypeCount]
    # 移除 difficulty_distribution
```

### 2.2 培训讲师汇总

```
GET /api/v1/exams/admin/trainers/summary?q=xxx&start_date=2026-01-01&end_date=2026-06-30
```

**新增 Query 参数**：
- `q`: string (optional) — 搜索讲师姓名或课程名称（模糊匹配）
- `start_date`: string (YYYY-MM-DD, optional) — 筛选考试 start_at >= start_date
- `end_date`: string (YYYY-MM-DD, optional) — 筛选考试 start_at <= end_date

**改造逻辑** (`get_trainer_summary`)：
- 添加时间范围筛选（过滤 exam.start_at）
- 添加搜索筛选（过滤 trainer_name 或 exam_name，ilike）
- 返回数据结构改为按讲师分组

**Schema 变更**：
```python
class TrainerExamItem(BaseModel):
    exam_id: uuid.UUID
    exam_name: str
    center: str | None
    start_at: datetime
    participant_count: int

class TrainerGroup(BaseModel):
    trainer_id: str
    trainer_name: str
    exam_count: int
    total_participants: int
    exams: list[TrainerExamItem]

class TrainerSummaryResponse(BaseModel):
    data: list[TrainerGroup]
    count: int  # 讲师数量
```

## 3. 前端改造

### 3.1 系统总览页面

**文件**: `frontend/src/tools/workbench/system_dashboard/components/SystemDashboardPage.tsx`

**新增组件**：
- 时间筛选区域：快捷选项按钮组（近7天 / 近30天 / 近90天 / 本年度 / 自定义）
- 自定义日期范围：两个日期选择器（开始日期 / 结束日期）

**移除**：
- 题库难易度占比饼图及其相关代码

**布局调整**：
- 移除难度分布图表后，图表区域改为 2 列（设备终端分布 + 题型分布）

### 3.2 培训讲师汇总页面

**文件**: `frontend/src/tools/workbench/trainer_summary/components/TrainerSummaryPage.tsx`

**改造内容**：
- 搜索框：支持搜索讲师姓名或课程名称
- 时间筛选：与系统总览相同的快捷选项 + 自定义日期范围
- 展示方式：从表格改为按讲师分组卡片
  - 每个讲师一个 Card
  - Card Header：讲师姓名 + 授课次数 + 总培训人数
  - Card Content：该讲师的考试列表（表格形式，列：课程名称、中心、考试时间、培训人数）
  - 课程名称可点击跳转考试详情
  - 考试按时间倒序排列

**新增接口类型**：
```typescript
interface TrainerExamItem {
  exam_id: string
  exam_name: string
  center: string | null
  start_at: string
  participant_count: number
}

interface TrainerGroup {
  trainer_id: string
  trainer_name: string
  exam_count: number
  total_participants: number
  exams: TrainerExamItem[]
}
```

## 4. 任务分解

### 后端任务
1. **系统总览 API 改造**
   - `schemas.py`: 移除 `DifficultyCount` 和 `SystemDashboardStats.difficulty_distribution`
   - `service.py`: `get_system_stats()` 增加 start_date/end_date 参数，时间范围筛选逻辑
   - `router.py`: `/admin/dashboard/stats` 增加 start_date/end_date query 参数

2. **培训讲师汇总 API 改造**
   - `schemas.py`: 新增 `TrainerExamItem`, `TrainerGroup`，改造 `TrainerSummaryResponse`
   - `service.py`: `get_trainer_summary()` 增加 q/start_date/end_date 参数，按讲师分组逻辑
   - `router.py`: `/admin/trainers/summary` 增加 q/start_date/end_date query 参数

### 前端任务
1. **系统总览页面改造**
   - 新增时间筛选组件（快捷选项 + 自定义日期）
   - 移除题库难易度占比图表
   - 调整图表布局为 2 列
   - API 调用增加日期参数

2. **培训讲师汇总页面改造**
   - 新增搜索框
   - 新增时间筛选组件
   - 从表格展示改为按讲师分组卡片展示
   - 更新 API 类型定义

### 测试任务
1. Playwright 验收测试系统总览时间筛选和图表变更
2. Playwright 验收测试培训讲师汇总分组展示、搜索、时间筛选
