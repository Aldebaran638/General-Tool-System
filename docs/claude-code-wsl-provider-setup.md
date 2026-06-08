# Claude Code WSL 本地代理配置说明

本文记录 Claude Code 在 WSL 中使用本地代理/第三方 Anthropic 兼容服务的配置流程。

## 1. 问题现象

在 WSL bash 中启动 `claude` 后，Claude Code 的 Bash 环境异常：

- `ls`、`mkdir`、`whoami`、`tr`、`sort` 等基础命令找不到。
- 找不到命令时响应很慢。
- Claude Code 显示 shell 为 Git Bash 的 `/bin/bash.exe`。
- 项目路径是 WSL 路径，但 Claude Code 读取 Windows 侧配置。

根因是 WSL 中的 `claude` 命令命中了 Windows npm shim：

```bash
command -v claude
```

异常输出类似：

```text
/mnt/c/Users/winkey/AppData/Roaming/npm/claude
```

该 shim 最终会执行 Windows 版 `claude.exe`，导致执行链变成：

```text
WSL bash -> Windows claude shim -> Windows claude.exe -> Git Bash -> Windows PATH
```

## 2. 安装 WSL 版 Claude Code

在 WSL 中安装 Linux 版 Claude Code：

```bash
npm install -g @anthropic-ai/claude-code
```

确认 WSL npm 全局 bin 在 PATH 前面：

```bash
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
hash -r
```

验证：

```bash
command -v claude
claude --version
```

正常输出应类似：

```text
/home/winkey/.npm-global/bin/claude
2.1.159 (Claude Code)
```

## 3. 配置代理环境变量

不要把 token 长期依赖在项目文件中。建议把用户级 Claude Code 环境放到：

```text
~/.claude-env
```

示例内容：

```bash
export ANTHROPIC_BASE_URL="https://your-provider.example.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="your-token"
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
export ANTHROPIC_MODEL="your-model"
export ANTHROPIC_DEFAULT_SONNET_MODEL="your-model"
export ANTHROPIC_DEFAULT_OPUS_MODEL="your-model"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="your-model"
```

设置权限：

```bash
chmod 600 ~/.claude-env
```

## 4. 让 WSL shell 自动加载配置

在 `~/.bashrc` 文件顶部、交互 shell 判断之前加入：

```bash
if [ -f "$HOME/.claude-env" ]; then
    . "$HOME/.claude-env"
fi
```

在 `~/.profile` 中也加入：

```bash
if [ -f "$HOME/.claude-env" ]; then
    . "$HOME/.claude-env"
fi
```

这样 login shell、interactive shell 和部分脚本入口都能继承 Claude Code 代理配置。

## 5. 清理 Anthropic 官方登录状态

如果 Claude Code 仍然跳转 Anthropic 登录，先退出官方 OAuth：

```bash
claude auth logout
```

然后重新打开 WSL 终端，或执行：

```bash
source ~/.bashrc
```

## 6. 验证配置

确认当前环境：

```bash
command -v claude
claude --version
env | grep '^ANTHROPIC_'
```

确认基础命令可用：

```bash
command -v bash
command -v git
command -v mkdir
command -v whoami
pwd
```

发一个最小请求：

```bash
claude -p "只回复 OK"
```

如果需要确认请求是否走代理，可以临时开启 debug：

```bash
rm -f /tmp/claude-debug.log
claude --debug-file /tmp/claude-debug.log -p "只回复 OK"
grep -E 'ANTHROPIC_BASE_URL|API REQUEST|anthropic' /tmp/claude-debug.log
```

正常情况下，应能看到配置的 `ANTHROPIC_BASE_URL`，并且请求成功返回 `OK`。

## 7. 注意事项

- 项目在 WSL 时，Claude Code 也应使用 WSL 版，不要使用 Windows 版操作 WSL 项目。
- 不要手改 `C:\Users\<user>\.claude\shell-snapshots\snapshot-*.sh`，这是 Claude Code 生成的环境快照，可能被覆盖。
- 不要提交 token。当前项目的 `.gitignore` 已忽略 `.claude/**`。
- 如果 `command -v claude` 又变回 `/mnt/c/.../claude`，说明 PATH 顺序被 Windows npm 路径抢先，需要重新把 `$HOME/.npm-global/bin` 放到 PATH 前面。
- 如果粘贴图片后出现模型不存在或无权限错误，通常是当前代理模型不支持图片输入。先新开 Claude Code 会话并只发送文本；需要图片能力时，改用代理侧明确支持视觉输入的模型。
