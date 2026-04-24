# FineReport Builder — Claude Code Skills for 帆软报表开发

将帆软报表开发经验沉淀为可复用的 **Claude Code Skills**，复制到任意项目即可直接使用。

## 核心产品：`.claude/skills/`

将以下目录复制到你的项目 `.claude/` 下，就能在 Claude Code 中开发帆软报表：

```
你的项目/.claude/skills/
├── cpt-knowledge.md      # 知识库 — CPT XML 标签结构、控件、样式系统
├── cpt-create.md         # 创建报表 — 从零生成完整 .cpt 文件
├── cpt-modify.md         # 修改报表 — 增删筛选组件、数据列、参数
└── cpt-validate.md       # 验证报表 — 检查帆软规范合规性
```

## 使用方式

### 1. Claude Code 对话（推荐）

在 Claude Code 中直接描述需求，自动触发对应 Skills：

```
"创建一个销售报表，数据源是 ClassTableData com.xx.SalesData，
 筛选条件：日期范围、区域下拉，展示：订单号、金额、状态"
```

Claude Code 会自动加载 `cpt-knowledge` → `cpt-create` → `cpt-validate` 工作流。

### 2. 命令行工具

```bash
# 生成报表
python cpt_tools/generate.py --config config.json --output report.cpt

# 修改现有报表
python cpt_tools/generate.py --modify report.cpt \
    --add-filters '[{"label":"区域","code":"region","type":"ComboBox"}]' \
    --add-columns '[{"header":"区域","field":"region"}]' \
    --output modified.cpt

# 校验报表
python cpt_tools/validate.py report.cpt
```

### 3. 本地代码引用

```python
from parsers.cpt_generator import CPTGenerator
from cpt_tools.validate import validate_cpt

# 生成
generator = CPTGenerator()
cpt = generator.generate(config)

# 校验
result = validate_cpt("report.cpt")
```

## 工作流

```
Claude Code 对话
  ↓
/cpt-knowledge    理解 CPT XML 结构
/cpt-create       生成 .cpt 文件
/cpt-validate     校验规范
/cpt-modify       迭代调整
```

## 项目结构

| 目录 | 定位 | 说明 |
|------|------|------|
| `.claude/skills/` | **核心交付物** | 可复制到其他项目的 Skills 包 |
| `cpt_tools/` | 命令行工具 | 生成、校验，可独立使用或被 Skills 调用 |
| `parsers/` | 解析器库 | CPT 生成/解析、ClassTableData 支持，供 tools 调用 |
| `templates/` | 知识文档 | CPT XML 模板结构详解，Skill 的知识引用 |
| `web/` | 测试工具 | 验证 Skills 生成的 CPT 是否正确，非交付物 |

## 核心约束

- **数据源参数只能多不能少**：筛选组件必须覆盖所有空值参数
- **ClassTableData 必须有 `<Parameters>` 节点**
- **`<O>` 标签必须用 CDATA 格式**：`<O><![CDATA[value]]></O>`
- **样式索引必须在 StyleList 范围内**
- **筛选组件布局**：每行 5 对（Label 89px + Input 135px），间距 4px，行间距 8px

## License

MIT
