# 功能设计文档：站内消息提醒系统（小邮箱）

## 需求概述

开发一个站内消息提醒系统（"小邮箱"），支持以下提醒场景：

1. **考试开考前1小时自动提醒** — 给未开始考试的参与者发送提醒
2. **考试开考自动提醒** — 考试开始时给未开始考试的参与者发送提醒
3. **考试未完成自动提醒** — 考试进行50%时间后，给未完成的参与者发送提醒
4. **考试未及格手动提醒** — 管理员在考试统计页面手动发送提醒

## 技术方案

- **消息存储**：数据库表 `notification`
- **定时调度**：复用现有 APScheduler（`backend/app/modules/data_sync/scheduler.py`）
- **消息渠道**：仅站内消息（小邮箱），不发送邮件
- **前端展示**：顶部导航栏消息角标 + 消息列表抽屉

---

## 数据库模型

```python
class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    title: str = Field(max_length=255)
    content: str = Field(sa_column=Column(Text))
    notification_type: str = Field(max_length=32, index=True)
    # EXAM_UPCOMING / EXAM_STARTED / EXAM_INCOMPLETE / EXAM_FAILED / ADMIN_BROADCAST

    is_read: bool = Field(default=False)

    # 关联信息
    exam_id: uuid.UUID | None = Field(default=None, foreign_key="exam.id")
    exam_name: str | None = Field(default=None, max_length=255)  # 快照，避免考试删除后丢失信息

    created_at: datetime = Field(default_factory=_utcnow, sa_type=DateTime(timezone=True))
    read_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
```

---

## 后端 API

### 通知管理（所有用户）

```
GET    /api/v1/notifications          — 获取当前用户的通知列表（支持分页、筛选已读/未读）
POST   /api/v1/notifications/{id}/read — 标记单条通知为已读
POST   /api/v1/notifications/read-all  — 标记所有通知为已读
DELETE /api/v1/notifications/{id}      — 删除单条通知
GET    /api/v1/notifications/unread-count — 获取未读通知数量（用于角标）
```

### 管理员手动提醒

```
POST /api/v1/exams/{exam_id}/remind-incomplete — 手动提醒未完成考试的人员
POST /api/v1/exams/{exam_id}/remind-failed     — 手动提醒未及格人员
```

---

## 定时任务（APScheduler）

### 1. 考试开考前1小时提醒

**频率**：每 5 分钟运行一次
**逻辑**：
- 查询 `start_at` 在 `(now + 55min, now + 65min)` 范围内的 PUBLISHED 考试
- 对每个考试，查询 completion_status = NOT_STARTED 的参与者
- 给每个参与者发送 `EXAM_UPCOMING` 类型通知
- **去重**：同一考试同一用户只发送一次（通过 exam_id + user_id + type 检查）

### 2. 考试开考提醒

**频率**：每 1 分钟运行一次
**逻辑**：
- 查询 `start_at` 在 `(now - 1min, now + 1min)` 范围内的 PUBLISHED 考试
- 对每个考试，查询 completion_status = NOT_STARTED 的参与者
- 给每个参与者发送 `EXAM_STARTED` 类型通知
- **去重**：同一考试同一用户只发送一次

### 3. 考试进行中50%提醒

**频率**：每 5 分钟运行一次
**逻辑**：
- 查询当前正在进行中的 PUBLISHED 考试（`start_at <= now < end_at`）
- 检查考试的已进行时间是否 >= 总时长的 50%
- 查询 completion_status != COMPLETED 的参与者
- 给每个参与者发送 `EXAM_INCOMPLETE` 类型通知
- **去重**：同一考试同一用户只发送一次

---

## 前端设计

### 1. 消息角标（Header）

- 在顶部导航栏右侧添加消息图标（Bell）
- 显示未读消息数量红点角标
- 点击打开消息列表抽屉

### 2. 消息列表抽屉

- 从右侧滑出的抽屉（或下拉面板）
- 显示最近 20 条通知，按时间倒序
- 每条通知显示：类型图标、标题、内容预览、时间、已读状态
- 支持：标记全部已读、删除单条、点击查看详情
- 底部有"查看全部"链接（跳转到消息中心页面）

### 3. 消息中心页面（可选，第一步不做）

- 完整的通知列表页面
- 支持筛选（全部/未读）、分页

### 4. 考试统计页面修改

- 在考试统计页面（`/exams/{id}/statistics`）添加按钮：
  - "提醒未完成人员" — 发送 EXAM_INCOMPLETE 提醒
  - "提醒未及格人员" — 发送 EXAM_FAILED 提醒
- 按钮只在考试已结束且有对应人员时显示

---

## 开发步骤

### 第一步：基础框架
- 数据库模型 `Notification`
- 后端 API（CRUD + 未读计数）
- 前端消息角标 + 抽屉
- 消息相关类型定义

### 第二步：自动提醒定时任务
- APScheduler 定时任务注册
- 开考前1小时提醒
- 考试开考提醒
- 考试进行中50%提醒

### 第三步：手动提醒 + 完善
- 考试统计页面添加手动提醒按钮
- 前端测试验证
- Code Review

---

## 验收标准

### 第一步验收
- [ ] 数据库 `notification` 表可正常创建
- [ ] API 可正常获取/标记已读/删除通知
- [ ] 前端消息角标显示未读数量
- [ ] 点击角标弹出消息列表抽屉
- [ ] 消息按时间倒序排列

### 第二步验收
- [ ] 发布一个1小时后开始的考试，添加参与者
- [ ] 约1小时后参与者收到"考试即将开始"通知
- [ ] 考试开始时参与者收到"考试已开始"通知
- [ ] 考试进行50%后未完成者收到"请尽快完成考试"通知
- [ ] 同一通知不重复发送

### 第三步验收
- [ ] 管理员在考试统计页面可点击"提醒未及格人员"
- [ ] 点击后未及格人员收到通知
- [ ] 所有功能 Playwright 验证通过
