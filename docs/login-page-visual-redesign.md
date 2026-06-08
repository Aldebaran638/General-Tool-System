# 登录页视觉重构设计文档

## 需求概述
优化登录页左右分屏的视觉体验，解决当前存在的 Logo 对比度不足、统计面板单调、右侧表单层级不清等问题。

## 设计目标
1. 左侧品牌面板：增强 Logo 辨识度，统计格子增加图标和微渐变层次
2. 右侧登录表单：优化标题层级，增强输入框聚焦反馈
3. 整体色调：保持蓝色系品牌调性，但增加视觉丰富度

## 具体改动

### 1. AuthLayout.tsx — 左侧品牌面板

#### 1.1 Logo 容器对比度优化
- 当前：`rounded-2xl bg-white/10 p-4 backdrop-blur-sm`
- 改为：`rounded-2xl bg-white/15 p-4 backdrop-blur-md border border-white/20 shadow-lg shadow-black/10`
- 目的：让 Logo 图标从蓝色背景中"浮"出来

#### 1.2 标题字间距优化
- 主标题增加 `tracking-wider` 字间距，增强品牌感
- 副标题保持现状或微调透明度

#### 1.3 统计格子增强
为每个统计指标增加 Lucide 图标，并用不同的微渐变背景区分：

| 指标 | 图标 | 渐变方向 |
|------|------|----------|
| 累计培训人次 | Users | from-white/15 to-blue-400/10 |
| 考试场次 | ClipboardList | from-white/15 to-indigo-400/10 |
| 考核通过 | Trophy | from-white/15 to-emerald-400/10 |
| 参与部门 | Building2 | from-white/15 to-violet-400/10 |

- 每个格子增加图标在数字上方
- 数字字体改用 `font-extrabold`，增加 `text-3xl`
- 标签文字增加 `font-medium`
- hover 效果：`hover:scale-[1.02] hover:bg-white/20`

#### 1.4 "实时数据"指示器增强
- 当前：文字 `text-xs text-blue-200/70`
- 改为：`text-sm text-blue-100/80 font-medium`
- 脉冲点加大到 `h-2 w-2`

#### 1.5 背景渐变微调
- 当前：`from-blue-600 via-blue-700 to-indigo-800`
- 改为：`from-blue-500 via-blue-700 to-indigo-900`
- 增加更多装饰光晕层次

### 2. login.tsx — 右侧登录表单

#### 2.1 标题层级优化
- "欢迎回来"：`text-2xl font-bold tracking-tight` → `text-3xl font-bold tracking-tight`
- 副标题：`text-sm text-muted-foreground` → `text-sm text-muted-foreground/80`
- 增加微妙的顶部间距让视觉更居中

#### 2.2 输入框聚焦色调整
- 当前：`focus-visible:ring-2 focus-visible:ring-primary/20`
- 改为：`focus-visible:ring-2 focus-visible:ring-blue-500/30 focus-visible:border-blue-400/50`
- 让聚焦色与左侧品牌蓝呼应

#### 2.3 登录按钮
- 增加 `shadow-sm hover:shadow-md hover:-translate-y-0.5` 微动效

## 文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `frontend/src/components/Common/AuthLayout.tsx` | 修改 | 品牌面板视觉重构 |
| `frontend/src/routes/login.tsx` | 修改 | 登录表单视觉优化 |

## 验收标准

1. 登录页在 1920x1080、1366x768、375x812（移动端）三种分辨率下显示正常
2. Logo 图标在左侧蓝色背景上清晰可见
3. 四个统计格子各有不同的微渐变背景和图标
4. 输入框聚焦时呈现蓝色系 ring 效果
5. Dark/Light 模式切换后整体视觉协调
