# 中心/部门层级管理功能设计文档

## 1. 功能概述

改造现有的企微部门同步和考试参与人管理功能，明确区分"中心"（一级部门）和"部门"（二级部门）两个层级。三级及以下部门标记为无效，不参与业务逻辑。

## 2. 需求背景

当前系统中，从企微同步的部门树包含所有层级，但用户的组织架构是：
- 根部门 = 公司名称（如 aldebaran）
- 一级部门 = 中心（如 部门1、部门2）
- 二级部门 = 部门（如 部门213213）
- 三级及以下 = 无效（如 小组A）

## 3. 后端改造

### 3.1 数据库模型变更

**`wecom_department` 表增加 `level` 字段：**

```python
class WecomDepartment(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str = Field(max_length=128)
    name_en: str | None = Field(default=None, max_length=128)
    parentid: int | None = Field(default=None, index=True)
    order: int = Field(default=0)
    level: int = Field(default=0)  # 新增: 1=中心, 2=部门, 3+=无效
    synced_at: datetime = ...
```

### 3.2 Alembic Migration

创建 migration 文件：
1. 添加 `level` 列到 `wecom_department` 表，默认值为 0
2. 遍历所有已有记录，根据 `parentid` 层级关系计算 level：
   - 找出根部门（parentid=1 或 parentid 为 null）
   - 根部门的直接子部门 = level 1（中心）
   - level 1 的直接子部门 = level 2（部门）
   - 其他 = level 3（无效）

### 3.3 部门同步改造

修改 `sync_departments()` 函数：
- 同步时计算每个部门的 level
- 计算逻辑：
  1. 找出根部门（parentid 为 null 或 parentid=1，假设根部门 id=1）
  2. 根部门的直接子部门 level=1（中心）
  3. level=1 部门的直接子部门 level=2（部门）
  4. 其余 level=3（无效）

### 3.4 成员同步改造

修改 `sync_members()` 函数：
- 成员同步后，过滤每个成员的 `department` 字段
- 只保留 level=1 或 level=2 的部门 ID
- 如果过滤后 department 为空，保留原值（避免数据丢失）

### 3.5 API 端点改造

**新增端点：**

```
GET /api/v1/data-sync/wecom-centers
```
- 仅返回 level=1 的部门（中心）
- 支持搜索（q 参数）

```
GET /api/v1/data-sync/wecom-departments
```
- 仅返回 level=2 的部门（部门）
- 支持搜索（q 参数）

**改造现有端点：**

```
GET /api/v1/data-sync/wecom-departments (现有)
```
- 增加可选过滤参数 `?level=1|2|3`
- 默认不过滤（保持向后兼容）

### 3.6 考试参与人添加接口

现有接口 `POST /exams/{exam_id}/participants/by-centers` 和 `POST /exams/{exam_id}/participants/by-departments` 逻辑不变，但前端传入的 ID 集合已通过新的 API 端点过滤。

## 4. 前端改造

### 4.1 新增 API 封装

在 `frontend/src/tools/data_sync/_shared/api.ts` 中新增：

```typescript
export function getCenters(page = 1, limit = 100, q?: string): Promise<WecomDepartmentsResponse>
export function getDepartmentsOnly(page = 1, limit = 100, q?: string): Promise<WecomDepartmentsResponse>
```

### 4.2 数据同步页面改造

**`WecomDepartmentSyncPage` / `SyncPage`：**

已同步数据 tab 中：
- 分两个区域展示：中心列表 + 部门列表
- 中心列表：只显示 level=1 的部门
- 部门列表：只显示 level=2 的部门
- 三级及以下部门不显示

### 4.3 考试详情页 - 添加参与人改造

**`ExamDetailPage` - ParticipantsTab：**

将当前的三个按钮（按中心/按部门/按人员）改造为：

**方案：平铺展示**

添加参与人区域改为：
- 上方："按中心添加" 区域
  - 展示所有 level=1 的中心（可搜索、可多选 checkbox）
  - 选择后点击"添加"按钮
- 下方："按部门添加" 区域
  - 展示所有 level=2 的部门（可搜索、可多选 checkbox）
  - 选择后点击"添加"按钮
- 右侧/下方："按人员添加" 区域（保持现有搜索框）

改造 DepartmentSearchSelect 组件或新建 CenterDepartmentSelect 组件：
- 支持传入 `level` 参数过滤
- 用 checkbox 列表展示（类似多选框），替代当前的搜索+下拉选择

## 5. 任务分解

### 后端任务
1. **模型变更**: `backend/app/modules/data_sync/models.py` - WecomDepartment 增加 level 字段
2. **迁移脚本**: 创建 Alembic migration，给历史记录补算 level
3. **同步改造**: `backend/app/modules/data_sync/service.py`
   - sync_departments() 同步时计算 level
   - sync_members() 过滤成员的 department 字段
4. **API 改造**: `backend/app/modules/data_sync/router.py`
   - 新增 `/wecom-centers` 和 `/wecom-departments` 端点
   - 现有 `/wecom-departments` 增加 level 过滤参数
5. **Schema 更新**: `backend/app/modules/data_sync/schemas.py` - 如有需要增加相关 schema

### 前端任务
1. **API 封装**: `frontend/src/tools/data_sync/_shared/api.ts` - 新增 getCenters/getDepartmentsOnly
2. **数据同步页面**: `frontend/src/tools/data_sync/_shared/SyncPage.tsx`
   - 已同步数据 tab 分中心/部门两个区域展示
3. **考试详情页**: `frontend/src/tools/exam/exam_management/components/ExamDetailPage.tsx`
   - ParticipantsTab 改造为平铺展示中心和部门
4. **组件改造/新建**: 修改 DepartmentSearchSelect 或新建多选 checkbox 组件

### 测试任务
1. 运行后端测试确保无回归
2. Playwright 验收测试：
   - 数据同步页面展示正确
   - 考试添加参与人功能正常
