# 功能设计文档：考试复制 + 我的待考组件

## 需求概述

1. **考试复制功能**：管理员在考试管理列表页可以复制某个考试，生成一个包含相同信息、试卷和参与人员的副本（状态为 DRAFT）。
2. **我的待考组件**：普通用户 Dashboard 首页显示当前用户参与的、未完成的已发布考试，正在进行中的优先展示。

---

## 第一步：考试复制功能

### 后端设计

#### 新增 API

```
POST /api/v1/exams/{exam_id}/clone
```

**权限**：RequireExamAdmin（SUPER_ADMIN 或 EXAM_ADMIN）

**逻辑**：
1. 根据 `exam_id` 获取原考试（Exam）
2. 创建新 Exam 记录：
   - 新生成 UUID
   - `name` = 原名称 + "（副本）"
   - `status` = "DRAFT"
   - `created_by` = 当前用户 ID
   - `published_at` = None
   - `created_at` / `updated_at` = now
   - 其他字段与原考试相同
3. 复制 Question 和 QuestionOption：
   - 每个 Question 生成新 UUID
   - 更新 `exam_id` 为新考试 ID
   - 每个 QuestionOption 生成新 UUID
   - 更新 `question_id` 为新 Question ID
4. 复制 ExamParticipant：
   - 每条记录生成新 UUID
   - 更新 `exam_id` 为新考试 ID
   - `completion_status` 重置为 "NOT_STARTED"
   - `final_score` / `final_passed` / `final_attempt_id` / `completed_at` 重置为 None
5. **不复制**：ExamAttempt、ExamAnswer、ExamPaper、ExamPaperSnapshot

**响应**：新创建的 ExamPublic

#### 修改文件
- `backend/app/modules/exam_management/router.py` — 新增 clone 路由
- `backend/app/modules/exam_management/service.py` — 新增 clone_exam 函数
- `backend/app/modules/exam_management/schemas.py` — 如有需要新增 schema

### 前端设计

#### 修改文件
- `frontend/src/tools/exam/exam_management/api.ts` — 新增 `cloneExam(id)` API 函数
- `frontend/src/tools/exam/exam_management/components/ExamListPage.tsx` — 在 DropdownMenu 中添加"复制"选项

#### UI 交互
- 在考试列表每行的操作菜单（DropdownMenu）中新增"复制"项
- 点击后调用 `cloneExam`，成功后 toast 提示"复制成功"并刷新列表
- 新副本名称自动为"原名称（副本）"

---

## 第二步：我的待考组件

### 后端设计

#### 新增 API

```
GET /api/v1/exams/my-pending
```

**权限**：CurrentUser（任何已登录用户）

**逻辑**：
1. 获取当前用户的 `userid`（优先使用 `wecom_userid`，否则用 `id`）
2. 查询条件：
   - `ExamParticipant.userid == current_userid`
   - `Exam.status == "PUBLISHED"`
   - `ExamParticipant.completion_status != "COMPLETED"`
   - `Exam.end_at > now`（考试尚未结束）
3. 排序：
   - 优先按 `Exam.start_at <= now AND Exam.end_at > now`（正在进行中的）排在前面
   - 其次按 `Exam.start_at` 升序

**响应**：简化版的考试列表（只需要名称、开始时间、结束时间、考试ID）

```typescript
interface MyPendingExam {
  id: string
  name: string
  start_at: string
  end_at: string
  is_in_progress: boolean  // 是否正在进行中
}
```

#### 修改文件
- `backend/app/modules/exam_management/router.py` — 新增 my-pending 路由
- `backend/app/modules/exam_management/service.py` — 新增 get_my_pending_exams 函数
- `backend/app/modules/exam_management/schemas.py` — 新增 MyPendingExams schema

### 前端设计

#### 修改文件
- `frontend/src/tools/exam/exam_management/api.ts` — 新增 `getMyPendingExams()` API 函数
- `frontend/src/routes/_layout/index.tsx` — Dashboard 中添加 `MyPendingExams` 组件

#### UI 设计
- 在非管理员用户的 Dashboard 中，显示"我的待考"卡片
- 卡片内容：
  - 标题："我的待考"
  - 列表：考试名称 + 状态标签（进行中/未开始）+ 截止时间
  - 点击考试名称进入考试页面
- 如果没有任何待考考试，显示空状态提示

---

## 验收标准

### 第一步验收
- [ ] 管理员在考试列表页可以看到"复制"按钮
- [ ] 点击复制后生成新考试，名称为"原名称（副本）"
- [ ] 新考试包含原考试的所有题目和选项
- [ ] 新考试包含原考试的参与人员列表
- [ ] 新考试状态为 DRAFT
- [ ] 复制后刷新列表，新考试出现在列表中

### 第二步验收
- [ ] 普通用户登录后 Dashboard 显示"我的待考"卡片
- [ ] 卡片中列出该用户参与的、未完成的已发布考试
- [ ] 正在进行中的考试排在前面
- [ ] 点击考试名称可以进入考试
- [ ] 没有待考考试时显示空状态
