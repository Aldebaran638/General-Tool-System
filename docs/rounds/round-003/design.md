# Round 003 Design - frontend_i18n

## 架构建议

本轮采用轻量前端 i18n，不引入后端依赖。

建议新增目录：

```text
frontend/src/i18n/
├── index.tsx
├── locales.ts
├── dictionaries/
│   ├── zh-CN.ts
│   ├── en-US.ts
│   └── zh-TW.ts
└── keys.ts
```

## Provider

新增 `I18nProvider`：

- 初始化 locale。
- 从 localStorage 读取 `app_locale`。
- 未设置时根据 `navigator.language` 推断。
- 提供 `locale`、`setLocale`、`t(key, params?)`。
- 语言切换写回 localStorage。

在应用根部挂载 Provider。具体位置由现有前端结构决定，必须覆盖所有路由。

## 翻译函数

建议接口：

```ts
const { t, locale, setLocale } = useI18n()
t("finance.invoiceFiles.title")
```

要求：

- 缺失 key 时开发环境可显示 key，避免静默失败。
- 支持简单参数插值，例如 `{count}`。

## 字典策略

业务 code 不变：

- `transportation`
- `meals_entertainment`
- `car_expenses`
- `other_project_expenses`
- `general_invoice`
- `vat_special_invoice`
- `toll_invoice`
- `draft`
- `confirmed`
- `voided`

显示文案通过翻译 key 获得，例如：

```ts
t(`finance.invoiceFiles.invoiceType.${invoiceType}`)
```

如果为了类型安全，也可以提供 helper：

```ts
getInvoiceTypeLabel(type, t)
```

## 改造范围

必须改造：

- `frontend/src/config/tool-navigation.tsx`
- `frontend/src/tools/registry.ts`
- `frontend/src/routes/_layout/settings.tsx`
- `frontend/src/routes/_layout/admin.tsx`
- `frontend/src/components/Admin/**`
- `frontend/src/components/Sidebar/**`
- `frontend/src/tools/finance/purchase_records/**`
- `frontend/src/tools/finance/invoice_files/**`
- 对应 Playwright 测试。

## 注意事项

- 不要在组件里写 `locale === "zh-CN" ? ...` 这种散乱判断。
- 不要把用户输入内容翻译。
- 不要修改 API payload 的 code。
- 不要引入需要后端配合的用户设置字段。
- 如果有现有英文平台组件，可逐步纳入同一字典。

