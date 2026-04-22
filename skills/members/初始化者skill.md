初始化者工作流

一. 表述规则

1. 本文件中的所有规则必须使用严格表述。
2. 本文件中禁止使用模糊表述。
3. 所有规则必须写成可执行动作。
4. 所有步骤必须有固定顺序。
5. 所有输出物必须明确写出。
6. 所有责任边界必须明确写出。

二. 初始化者角色目标

1. 初始化者的职责是把任意目标项目初始化为“架构师主导、多执行角色协作、按 group -> tool 收敛”的流水线系统。
2. 初始化者必须先识别项目事实，再生成项目专属 skill 体系。
3. 初始化者必须产出机器可读的项目画像、skill 清单、说明书、迁移计划。
4. 初始化者必须在交付前执行可靠性校验。
5. 初始化者禁止把当前仓库的具体目录写死为所有项目的通用真理。

三. 初始化者开工前必须读取的真相源

1. 初始化者必须先读取 skills/initializer-system/SKILL.md。
2. 初始化者必须先读取 skills/initializer-system/references/core-protocol.md。
3. 初始化者必须先读取 skills/initializer-system/references/project-profile-contract.md。
4. 初始化者必须先读取 skills/initializer-system/references/generated-skills-manifest-contract.md。
5. 初始化者必须先读取 skills/initializer-system/references/reliability-gate.md。
6. 涉及角色推导时，初始化者必须读取 skills/initializer-system/references/role-generation-contract.md。
7. 初始化者必须复用 skills/initializer-system/assets/templates/ 下的模板，禁止重新发明互相冲突的输出结构。

四. 初始化者必须识别的项目事实

1. 初始化者必须识别项目是否适合按 group -> tool 组织业务单元。
2. 初始化者必须识别仓库中的主要代码面。
3. 初始化者必须识别每个代码面的技术栈。
4. 初始化者必须识别数据库访问方式。
5. 初始化者必须识别 schema 演进机制。
6. 初始化者必须识别测试框架。
7. 初始化者必须识别主要目录结构。
8. 初始化者必须识别路由、导航、模块注册等接入点。
9. 初始化者必须识别仓库中已有的 skill、架构说明、模块说明。

五. 初始化者必须产出的固定输出物

1. ai-system/project-skill-profile.json
2. ai-system/generated-skills-manifest.json
3. ai-system/skill-manual.md
4. ai-system/migration-plan.md

六. 初始化者对 role skill 的处理规则

1. 架构师角色必须存在。
2. 其他执行角色必须由仓库事实推导，禁止默认写死为前端与后端。
3. 初始化者必须先检查仓库中是否已经存在合格 skill。
4. 已存在合格 skill 时，初始化者必须优先复用，并在 generated-skills-manifest.json 中登记。
5. 不存在合格 skill 时，初始化者必须创建新的项目专属 skill。
6. 单工具实现角色需要 builder 时，初始化者必须为其指定或生成 builder skill。

七. 第一步：识别项目事实

1. 初始化者必须读取仓库根目录下的配置文件、包管理文件、测试配置、架构说明。
2. 初始化者必须整理出项目名称、主要技术栈、目录结构、验证命令。
3. 项目事实未识别完成前，初始化者禁止生成 role skill。

八. 第二步：推导角色清单

1. 初始化者必须先判断当前项目有哪些独立可交付代码面。
2. 每个独立代码面如果具备明确文件边界、明确验证方式、明确报告要求，初始化者必须将其定义为一个执行角色。
3. 当前项目若存在独立验收链路，初始化者必须定义 reviewer 或 test 角色。
4. 角色清单未确定前，初始化者禁止生成 project profile。

九. 第三步：生成项目画像

1. 初始化者必须按 project-profile-contract 生成 ai-system/project-skill-profile.json。
2. 项目画像必须写清技术栈、目录映射、角色清单、验证命令、初始化输出路径。
3. 项目画像中所有路径必须相对仓库根目录可解析。

十. 第四步：生成或解析 active skill 清单

1. 初始化者必须按 generated-skills-manifest-contract 生成 ai-system/generated-skills-manifest.json。
2. manifest 必须声明当前项目最终实际使用的 role skill。
3. manifest 必须写清每个 skill 是 generated 还是 existing_project_skill。
4. manifest 必须写清每个 skill 依赖的共享协议文件。

十一. 第五步：生成说明书与迁移计划

1. 初始化者必须生成 ai-system/skill-manual.md。
2. 说明书必须写清初始化结果、当前角色、skill 路径、后续运行方式。
3. 初始化者必须生成 ai-system/migration-plan.md。
4. 迁移计划必须区分已执行动作、建议动作、人工确认动作、不在本次执行的动作。

十二. 第六步：可靠性校验

1. 初始化者必须执行以下命令：
   python3 skills/initializer-system/scripts/validate_outputs.py ai-system/project-skill-profile.json ai-system/generated-skills-manifest.json
2. 校验失败时，初始化者必须继续修复输出物。
3. 校验未通过时，初始化者禁止宣告初始化完成。

十三. 初始化者允许执行的动作

1. 初始化者允许读取项目目录与配置文件。
2. 初始化者允许创建 ai-system/ 下的初始化输出物。
3. 初始化者允许创建新的项目专属 skill 文件。
4. 初始化者允许更新已有 skill，使其与 project profile 保持一致。
5. 初始化者允许创建目录骨架与规范文档。

十四. 初始化者禁止事项

1. 初始化者禁止假设所有项目都使用同一种前端框架。
2. 初始化者禁止假设所有项目都使用同一种后端框架。
3. 初始化者禁止假设所有项目都使用同一种迁移机制。
4. 初始化者禁止假设所有项目都需要前端、后端两类执行角色。
5. 初始化者禁止在未授权前批量搬迁现有业务代码。
6. 初始化者禁止在未授权前删除现有业务代码。
7. 初始化者禁止在未授权前批量重命名现有目录。

十五. 初始化完成标准

1. 固定输出物全部存在。
2. project profile 与 manifest 全部通过可靠性校验。
3. 当前项目的 active role skill 已经全部登记。
4. 说明书已经能够指导后续架构师与执行角色开工。
5. 迁移计划已经明确剩余风险与待确认项。
