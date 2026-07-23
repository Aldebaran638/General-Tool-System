# 飞书应用配置指南

本文说明如何把“项目管理面板”配置为飞书企业自建应用，并启用浏览器 OAuth 授权登录和工作汇报提醒。

当前实现使用飞书用户的 `open_id` 识别用户。用户第一次通过飞书登录时，系统会自动创建本地账号；后续使用同一飞书应用登录时会复用该账号。

## 1. 创建企业自建应用

1. 登录[飞书开放平台](https://open.feishu.cn/app)。
2. 进入“开发者后台”。
3. 选择“创建企业自建应用”。
4. 填写应用名称、描述和图标。

必须使用企业自建应用。应用仅供其所属企业内、且位于应用可用范围内的成员使用。

## 2. 获取应用凭证

进入应用的“凭证与基础信息”，复制：

- App ID
- App Secret

将它们写入项目根目录的 `.env`：

```dotenv
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

注意：

- App ID 和 App Secret 必须来自同一个应用。
- App Secret 只能保存在服务端，不得写入前端代码或提交到 Git。
- 更换 App Secret 后，需要同步更新 `.env`。

## 3. 配置重定向 URL

先确定用户实际访问项目的地址。本文将其记为 `{FRONTEND_ORIGIN}`，它必须包含协议和实际对外端口，但末尾不带 `/`。例如：

```text
本机开发：http://localhost:10305
局域网访问：http://192.168.1.20:10305
域名访问：https://pm.example.com
```

开发环境中，前端会把 `{FRONTEND_ORIGIN}/api/*` 代理到后端。因此，进入飞书应用的“安全设置”或“重定向 URL”页面，添加：

```text
{FRONTEND_ORIGIN}/api/v1/login/feishu/callback
```

并在 `.env` 中填写完全相同的完整地址。例如，本机开发配置为：

```dotenv
FRONTEND_HOST=http://localhost:10305
FEISHU_REDIRECT_URI=http://localhost:10305/api/v1/login/feishu/callback
BACKEND_CORS_ORIGINS=http://localhost:10305
```

局域网使用 `192.168.1.20` 访问时，则三处都要使用同一个可访问地址：

```dotenv
FRONTEND_HOST=http://192.168.1.20:10305
FEISHU_REDIRECT_URI=http://192.168.1.20:10305/api/v1/login/feishu/callback
BACKEND_CORS_ORIGINS=http://192.168.1.20:10305
```

必须保证飞书后台与 `FEISHU_REDIRECT_URI` 的协议、主机、端口和路径完全一致。不要在同一次登录中混用 `localhost`、`127.0.0.1`、局域网 IP 或不同域名。

### 开发环境端口说明

| 地址 | 用途 | 是否填写到飞书回调 |
| --- | --- | --- |
| `http://{主机}:10305` | 前端页面；同时代理 `/api/*` 到后端 | 是，推荐 |
| `http://{主机}:10304` | 后端 API 的直连调试端口 | 否，通常不填写 |
| `http://backend:8000` | Docker 容器之间访问后端 | 否，浏览器无法访问 |

飞书授权完成后，是用户浏览器访问回调地址，而不是飞书服务器主动回调。因此：

- 本机开发使用 `localhost` 时，不需要内网穿透。
- 局域网内多人使用时，可以填写项目主机的局域网 IP，但用户必须能访问该 IP 和端口，且主机防火墙需要放行。
- 跨网络或正式使用时，需要用户浏览器能够访问的域名或其他可路由地址。

## 4. 配置权限

进入“权限管理”，开通：

| 权限名称 | 是否必需 | 用途 |
| --- | --- | --- |
| 获取用户身份标识 | 必需 | 获取当前登录用户的 `open_id` 和基础身份信息 |
| 以应用的身份发消息 | 使用汇报提醒时必需 | 由应用机器人向尚未提交汇报的员工发送提醒 |

当前项目不读取或绑定飞书邮箱，因此不需要“获取用户邮箱信息”。

当前项目也不需要以下权限：

- `profile:user_profile:read`
- `component:user_profile`
- 获取成员名片信息
- 通过手机号或邮箱获取用户 ID

不要在授权 URL 中手工填写 `user_profile` 等 scope。当前后端不传 `scope` 参数，由飞书根据应用已开通的登录权限完成授权。

## 5. 配置机器人能力

如果需要使用周报、月报提醒：

1. 进入“应用功能 > 机器人”，启用机器人能力。
2. 在“权限管理”中开通“以应用的身份发消息”。
3. 创建并发布包含上述能力与权限的新版本。
4. 确保接收提醒的员工位于应用可用范围内。

提醒由后端主动调用飞书 OpenAPI 发送，接收人使用登录时保存的 `open_id`。卡片中的“立即填写”按钮只是打开项目页面，因此不需要配置事件订阅、消息回调或卡片回传地址，也不需要内网穿透。服务器需要能够主动访问飞书开放平台。

更换飞书应用后，旧应用保存的 `open_id` 不能直接用于新应用。员工需要先使用新应用重新登录，建立新绑定后才能收到提醒。

## 6. 配置网页应用能力（可选）

如果希望用户从飞书工作台打开项目，需要进入“应用功能 > 网页应用”，启用网页应用并配置主页地址：

```text
{FRONTEND_ORIGIN}
```

该配置只影响从飞书工作台打开项目。仅通过浏览器访问项目并点击“使用飞书登录”时，不依赖工作台入口。

`localhost` 只适合开发者本人本机测试。其他员工使用时，应改为他们能够访问的局域网地址或域名。

## 7. 设置可用范围并发布

1. 进入“版本管理与发布”。
2. 创建新版本。
3. 设置应用可用范围，至少包含用于测试登录的账号。
4. 申请发布。
5. 由企业管理员在飞书管理后台完成审核。
6. 确认版本状态为“已发布”。

权限、回调地址或应用能力发生变化后，应根据飞书后台提示重新创建并发布版本。未发布的正式应用可能无法正常调用 OpenAPI。

## 8. 让项目配置生效

修改 `.env` 后，重新创建后端容器：

```bash
docker compose up -d --force-recreate backend
```

如果启用了汇报提醒，还需要重新创建提醒 worker：

```bash
docker compose up -d --force-recreate work-report-reminder
```

不需要重建数据库，也不需要重新构建前端。可以使用以下命令确认服务状态：

```bash
docker compose ps
docker compose logs --tail 100 backend
docker compose logs --tail 100 work-report-reminder
```

如果同时修改了 Compose 中的前端环境变量或前端构建参数，再重新创建前端容器：

```bash
docker compose up -d --force-recreate frontend
```

## 9. 验证登录

1. 浏览器打开 `{FRONTEND_ORIGIN}/login`。
2. 点击“使用飞书登录”。
3. 在飞书授权页确认授权。
4. 授权后，浏览器应依次返回后端回调地址和前端回调页面，最后进入系统主页。
5. 第一次登录的飞书用户会被自动注册为普通用户。

系统只保存飞书 `open_id` 和显示名称。自动生成的占位邮箱格式为：

```text
feishu-<摘要>@users.feishu.internal
```

该邮箱不是用户的真实邮箱。

## 10. 验证汇报提醒

1. 使用管理员账号进入“汇报提醒”。
2. 在“测试接收人”中明确选择一个已绑定飞书的启用用户；系统不会默认选择任何人。
3. 点击“发送测试卡片”，确认被选用户收到卡片。
4. 新建周报或月报提醒规则，设置时区、发送时间和适用成员。
5. 在“发送记录”查看命中人数、成功数、跳过数和失败原因。
6. 在“未绑定用户”查看暂时无法接收飞书消息的启用账号。

新部署默认不创建任何提醒规则。成员选择器只展示启用且已绑定飞书的用户；系统只检查规则所选成员，并提醒其中当前周期尚未提交相应汇报的用户。成员保存规则后失去飞书绑定时会记录为跳过。同一规则、同一周期、同一计划发送时间不会重复创建发送任务。

## 11. 更换飞书应用时的注意事项

同一个用户在不同飞书应用中的 `open_id` 不同。更换 App ID 后，系统可能把原用户识别为新用户并再次自动注册。

更换应用前，应确认是否需要迁移已有用户的飞书绑定关系。只修改 App ID 和 App Secret，不会自动把旧应用账号绑定到新应用账号。

## 12. 常见错误

### `20028 client_id 请求不合法`

优先检查：

- `.env` 中是否填写了新应用的 App ID。
- App ID 是否完整，是否多出空格或引号。
- App ID 与 App Secret 是否来自同一个应用。
- 应用是否已经发布并对当前用户可用。
- 修改 `.env` 后是否重新创建了后端容器。

该错误发生在授权页时，飞书尚未使用 App Secret，重点检查 App ID 和应用状态。

### `20043 user_profile 有误`

授权请求中包含了当前应用无法使用的 `user_profile` scope。当前项目不需要该 scope，不应手工添加。

### 重定向地址不合法或不一致

确认飞书后台与 `.env` 中的地址逐字一致。例如本机开发为：

```text
http://localhost:10305/api/v1/login/feishu/callback
```

### 授权成功但未进入主页

检查：

- `FRONTEND_HOST` 是否等于浏览器实际访问的前端来源。
- `FEISHU_REDIRECT_URI` 是否使用浏览器可访问的地址，并以 `/api/v1/login/feishu/callback` 结尾。
- 浏览器是否禁用了登录流程所需的 Cookie。
- 登录开始和回调过程是否始终使用同一个主机名。
- 后端日志中是否出现换取令牌或读取用户信息失败。

## 13. 正式环境

正式部署时，推荐由同一个 HTTPS 地址提供前端页面并把 `/api/*` 反向代理到后端：

```dotenv
FRONTEND_HOST=https://pm.example.com
FEISHU_REDIRECT_URI=https://pm.example.com/api/v1/login/feishu/callback
BACKEND_CORS_ORIGINS=https://pm.example.com
```

如果正式环境使用独立 API 域名，也可以把回调地址配置为：

```dotenv
FRONTEND_HOST=https://pm.example.com
FEISHU_REDIRECT_URI=https://api.example.com/api/v1/login/feishu/callback
BACKEND_CORS_ORIGINS=https://pm.example.com
```

此时必须确保 `api.example.com` 直接路由到后端，并允许后端回跳到 `FRONTEND_HOST`。无论使用哪种拓扑，飞书后台登记的地址都必须与 `FEISHU_REDIRECT_URI` 完全一致。

## 官方参考

- [创建企业自建应用](https://open.feishu.cn/document/integrating-web-apps-in-5-minutes/step-1-create-enterprise-self-built-applications?lang=zh-CN)
- [获取登录用户信息](https://open.feishu.cn/document/server-docs/authentication-management/login-state-management/get)
- [发送消息](https://open.feishu.cn/document/server-docs/im-v1/message/create)
- [未发版自建应用能力变更说明](https://open.feishu.cn/document/platform-notices/breaking-change/Call_OpenAPI_without_Auditing)
