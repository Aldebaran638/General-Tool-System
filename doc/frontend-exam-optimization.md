# 考试前端优化设计文档

## 1. 需求概述

优化考试相关前端页面，提升用户在考试数量较多时的使用体验：
1. "我的考试"页面添加搜索和筛选功能
2. 隐藏/弱化前端显示的 ID 信息

## 2. 详细设计

### 2.1 "我的考试"页面搜索优化 (ExamParticipationPage.tsx)

#### 搜索功能
- **搜索框**：按考试名称实时过滤（client-side）
  - 位置：Tabs 上方
  - 占位符："搜索考试名称..."
  - 图标：Search (lucide-react)

- **分类筛选**：下拉选择框
  - 位置：搜索框右侧
  - 选项：从后端获取分类列表 + "全部分类"
  - 依赖：需要调用 `listExamCategories` API

- **状态筛选**：下拉选择框
  - 位置：分类筛选右侧
  - 选项：全部状态 / 进行中 / 未开始 / 已结束 / 已完成 / 未通过
  - 说明：基于考试状态（status + completion_status + 时间计算）

#### 过滤逻辑
```
filteredExams = allExams
  .filter(e => search === "" || e.name.toLowerCase().includes(search.toLowerCase()))
  .filter(e => categoryFilter === "all" || e.category_id === categoryFilter)
  .filter(e => statusFilter === "all" || matchStatus(e, statusFilter))
```

#### 状态匹配规则
- `active`：进行中（now >= start && now <= end && status !== ARCHIVED）
- `upcoming`：未开始（now < start）
- `ended`：已结束（now > end || status === ARCHIVED）
- `completed`：已完成（completion_status === COMPLETED）
- `failed`：未通过（completion_status === NOT_COMPLETED && attempt_count > 0）

#### UI 调整
- 搜索和筛选栏放在 Tabs 上方
- 当前考试和历史记录分别应用过滤
- 空状态时显示友好提示（带搜索关键词时显示"未找到匹配的考试"）

### 2.2 ID 隐藏/弱化方案

#### 2.2.1 ExamDetailPage.tsx - 人员管理 Tab

**修改前：**
```
表格列：Userid | 姓名 | 中心 | 部门 | 添加时间 | 操作
```

**修改后：**
```
表格列：姓名 | 中心 | 部门 | 添加时间 | 操作
```
- 删除 Userid 列
- 调整列宽，确保信息完整显示

**用户标签修改：**
```tsx
// 修改前
<Badge>
  <span>{user.name}</span>
  <span className="text-xs text-muted-foreground">({user.userid})</span>
</Badge>

// 修改后
<Badge>
  <span>{user.name}</span>
  <span className="text-[10px] text-muted-foreground/60 ml-1">{user.userid}</span>
</Badge>
```

**部门/中心标签修改：**
```tsx
// 修改前
<Badge>
  <span>{dept.name}</span>
  <span className="text-xs text-muted-foreground">(ID: {dept.id})</span>
</Badge>

// 修改后
<Badge>
  <span>{dept.name}</span>
  <span className="text-[10px] text-muted-foreground/60 ml-1">ID: {dept.id}</span>
</Badge>
```

#### 2.2.2 ExamCategoryManagementPage.tsx

**修改前：**
```
表格列：ID | 名称 | 排序 | 创建时间 | 操作
```

**修改后：**
```
表格列：名称 | 排序 | 创建时间 | 操作
```
- 删除 ID 列
- 排序和创建时间左对齐

#### 2.2.3 TrainerSearchSelect.tsx

**修改前：**
```tsx
<div>
  <span className="font-medium">{user.name}</span>
  <span className="text-xs text-muted-foreground">{user.userid}</span>
</div>
```

**修改后：**
```tsx
<div>
  <span className="font-medium">{user.name}</span>
  <span className="text-[10px] text-muted-foreground/60">{user.userid}</span>
</div>
```

## 3. API 依赖

| API | 用途 | 是否已有 |
|-----|------|---------|
| `fetchMyExams` | 获取我的考试列表 | ✅ 已有 |
| `listExamCategories` | 获取分类列表用于筛选 | ✅ 已有 |

## 4. 组件修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `ExamParticipationPage.tsx` | 添加搜索框、分类筛选、状态筛选 | P0 |
| `ExamDetailPage.tsx` | 隐藏 Userid 列，弱化标签 ID | P1 |
| `ExamCategoryManagementPage.tsx` | 隐藏 ID 列 | P1 |
| `TrainerSearchSelect.tsx` | 弱化 userid 显示 | P1 |

## 5. 验收标准

1. "我的考试"页面可以按名称搜索考试
2. "我的考试"页面可以按分类和状态筛选
3. 所有页面不再直接显示 ID 列
4. 下拉列表中的 ID 使用弱化样式（灰色小字）
5. Playwright 手动测试无报错
6. UI 风格与现有系统保持一致
