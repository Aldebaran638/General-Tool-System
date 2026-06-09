# UI 优化 Round 2 — 全局页面美化

## 需求概述
基于系统页面截图巡检结果，对以下视觉问题进行集中修复和优化。

## 问题清单与修复方案

### 1. Dashboard 首页 — 从空白到工作台
**问题**：首页完全空白，只有问候语。

**设计**：
- 顶部：欢迎横幅（渐变背景）+ 当日日期
- 第一行：4 个快捷统计卡片（考试场次、试题数量、参与人次、及格率），带图标和趋势箭头
- 第二行：快捷入口区域，6 个功能卡片（考试管理、试题库、系统总览、培训讲师、用户管理、数据同步）
- 第三行：最近考试列表（取最近 5 条）

**文件**：`frontend/src/routes/_layout/index.tsx`

### 2. 404 页面 — 品牌化处理
**问题**：纯黑色 404 + Go Back，过于简陋。

**设计**：
- 背景使用与登录页一致的墨绿色渐变
- 中央放置公司 Logo（WINKEY）
- 大标题："页面走丢了" + 副标题 "您访问的页面不存在或已被移除"
- 两个按钮："返回首页"（primary）+ "返回上一页"（outline）
- 底部增加版权信息

**文件**：`frontend/src/routes/__root.tsx` 或查找现有 NotFound 组件

### 3. Sidebar "Appearance" 汉化
**问题**：底部显示英文 "Appearance"。

**修复**：将 `Appearance` 组件中的文案改为"主题"。

**文件**：`frontend/src/components/Common/Appearance.tsx`

### 4. 考试管理 — 时间格式优化
**问题**：考试时间占两行，撑高表格行。

**修复**：将时间格式改为单行，如 `06/05 16:21 ~ 22:27`，或只显示日期。

**文件**：`frontend/src/tools/exam/exam_management/components/ExamListPage.tsx`（或相关文件）

### 5. 系统总览 — 空状态优化
**问题**："考试终端分布"图表区域显示"暂无数据"，空白过大。

**修复**：
- 空状态增加占位插画（使用 Lucide 图标组合）
- 文案改为："暂无终端分布数据，请先创建考试并收集答题数据"

**文件**：`frontend/src/tools/workbench/system_dashboard/components/SystemDashboardPage.tsx`

### 6. 培训讲师汇总 — UUID fallback
**问题**：讲师名显示 UUID。

**修复**：如果 full_name 为空，fallback 显示 email 前缀（@ 前部分），再为空则显示"未知讲师"。

**文件**：`frontend/src/tools/workbench/trainer_summary/components/TrainerSummaryPage.tsx`

### 7. 页面顶部空白方块
**问题**：每个页面标题栏左侧有空白方块。

**修复**：检查 `Breadcrumb` 或 `PageHeader` 组件，移除或替换空图标。

**文件**：`frontend/src/components/Common/Layout.tsx` 或相关布局组件

## 文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `frontend/src/routes/_layout/index.tsx` | 重写 | Dashboard 工作台 |
| `frontend/src/routes/__root.tsx` 或 NotFound | 修改 | 404 品牌页面 |
| `frontend/src/components/Common/Appearance.tsx` | 修改 | 汉化 |
| `frontend/src/tools/exam/exam_management/components/ExamListPage.tsx` | 修改 | 时间格式 |
| `frontend/src/tools/workbench/system_dashboard/components/SystemDashboardPage.tsx` | 修改 | 空状态 |
| `frontend/src/tools/workbench/trainer_summary/components/TrainerSummaryPage.tsx` | 修改 | UUID fallback |
| `frontend/src/components/Common/Layout.tsx` | 修改 | 空白方块 |
| `frontend/public/assets/images/company-logo.png` | 新增 | 公司 Logo |

## 验收标准
1. Dashboard 有内容，不再空白
2. 404 页面有品牌元素
3. Sidebar "Appearance" 显示为"主题"
4. 考试管理时间显示为单行
5. 系统总览空状态有插画和引导文案
6. 讲师汇总不再显示 UUID
7. 页面顶部无空白方块
8. 所有页面通过 Playwright 视觉检查
