# FineReport Builder

基于 **Claude Code Skills** 的帆软报表（.cpt）自动化构建工具。

## 架构

```
.claude/skills/          ← Claude Code 指令集（知识库 + 4 个技能）
cpt_tools/               ← 命令行工具（生成 / 校验）
parsers/                 ← 核心解析器（CPT 生成 / 解析 / ClassTableData）
web/                     ← Web 服务（分析 / 测试 / 文件管理）
templates/               ← CPT 模板知识库（XML 结构详解）
```

## Claude Code Skills 使用

在 Claude Code 中通过 `/cpt-` 前缀触发：

| 指令 | 用途 |
|------|------|
| `/cpt-knowledge` | 加载帆软 CPT 知识库（XML 标签、控件、样式） |
| `/cpt-create` | 根据数据源、筛选条件、展示列创建新报表 |
| `/cpt-modify` | 基于现有 .cpt 增删组件、列、参数 |
| `/cpt-validate` | 验证 .cpt 文件是否符合帆规范 |

### 工作流

```
/cpt-knowledge → 理解 CPT 结构
/cpt-create    → 生成报表文件
/cpt-validate  → 校验输出结果
/cpt-modify    → 迭代调整（可选）
```

## 核心约束

- **数据源参数只能多不能少**：筛选组件必须覆盖所有空值参数
- **ClassTableData 必须有 `<Parameters>` 节点**
- **`<O>` 标签必须用 CDATA 格式**：`<O><![CDATA[value]]></O>`
- **样式索引必须在 StyleList 范围内**
- **筛选组件布局**：每行 5 对（Label 89px + Input 135px），间距 4px，行间距 8px

## Web 服务

```bash
pip install -r requirements.txt
python web/app.py --port 5002
```

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/` | Skills 概览、文件管理 |
| CPT 分析 | `/cpt-analyze` | 解析 .cpt 文件结构 |
| Class 测试 | `/class-test` | ClassTableData 交互测试 |
| API | `/api/v2/generate` | 报表生成接口（POST JSON） |

## 项目结构

```
fineReport-builder/
├── .claude/skills/
│   ├── cpt-knowledge.md      # 知识库：CPT XML 标签结构
│   ├── cpt-create.md         # 技能：从零创建报表
│   ├── cpt-modify.md         # 技能：修改现有报表
│   └── cpt-validate.md       # 技能：验证报表规范
├── cpt_tools/
│   ├── generate.py           # 命令行生成入口
│   └── validate.py           # 命令行校验入口
├── parsers/
│   ├── cpt_generator.py      # CPT XML 生成逻辑
│   ├── cpt_parser.py         # CPT XML 解析逻辑
│   └── class_table_data.py   # ClassTableData 解析/测试
├── templates/
│   └── CPT_TEMPLATE_ANNOTATION.md  # CPT 模板注释文档
├── web/
│   ├── app.py                # Flask 后端
│   └── templates/            # 前端页面
├── CLAUDE.md                 # 项目上下文
├── README.md
├── requirements.txt
└── .gitignore
```

## License

MIT
