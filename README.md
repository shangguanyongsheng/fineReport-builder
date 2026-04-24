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

## 使用方式一：Claude Code 对话（推荐）

### 场景 A：从零创建新报表

按顺序执行以下步骤：

**Step 1 — 加载知识库**

```
/cpt-knowledge
```

加载 CPT 文件结构、XML 标签规范、控件类型、样式系统等知识，让 Claude 理解帆软报表。

**Step 2 — 描述需求**

知识库加载完成后，描述你的报表需求：

```
我要创建一个合同明细报表：
- 数据源：ClassTableData，全路径 com.yocyl.fr.engine.tableData.finance.CreditContractDetailData
- 入参：orgId（空）、startDate（空）、endDate（空）
- 出参：contractNo, tenantName, amount, status
- 筛选组件：日期范围（startDate/endDate, DateEditor）、组织机构（orgId, TreeComboBoxEditor）
- 展示列：序号、合同编号、租户名称、金额、状态
```

Claude 会自动读取需求，理解数据源、筛选条件、展示列。

**Step 3 — 生成报表**

```
/cpt-create
```

根据前面的需求和知识，生成完整的 .cpt 文件。包括：
- 数据源配置（ClassTableData + Parameters 节点）
- 筛选组件（自动计算布局坐标）
- 表头和数据列单元格
- 样式绑定

**Step 4 — 验证**

```
/cpt-validate
```

检查生成的 .cpt 是否符合帆软规范：
- XML 结构完整性
- ClassTableData Parameters 节点存在
- `<O>` 标签 CDATA 格式
- 筛选组件 code 与数据源参数名匹配
- 样式索引不超出范围

### 场景 B：修改现有报表

**Step 1 — 加载知识库**

```
/cpt-knowledge
```

**Step 2 — 说明修改内容**

```
在 outputs/合同明细.cpt 基础上：
- 新增筛选组件：区域（region, ComboBox，选项：华东/华南/华北）
- 新增展示列：区域
- 数据源新增入参：region
```

**Step 3 — 执行修改**

```
/cpt-modify
```

基于现有 .cpt 模板，通过复制 XML 节点的方式增删组件，保持所有默认配置不变。

**Step 4 — 验证**

```
/cpt-validate
```

### 指令速查

| 指令 | 作用 | 什么时候用 |
|------|------|------------|
| `/cpt-knowledge` | 加载知识库 | 每次开始新任务时，首先执行 |
| `/cpt-create` | 从零创建报表 | 已有明确需求后，生成新 .cpt |
| `/cpt-modify` | 修改现有报表 | 在已有 .cpt 上增删改 |
| `/cpt-validate` | 验证报表规范 | 生成或修改完成后，必须执行 |

## 使用方式二：命令行工具

不依赖 Claude Code 对话，直接通过命令行生成和校验：

```bash
# 通过 JSON 配置生成报表
python cpt_tools/generate.py --config config.json --output report.cpt

# 通过 stdin 传入配置
echo '{"title":"测试","data_sources":[...],"cells":[...]}' | \
  python cpt_tools/generate.py --stdin --output report.cpt

# 修改现有报表
python cpt_tools/generate.py --modify report.cpt \
    --add-filters '[{"label":"区域","code":"region","type":"ComboBox"}]' \
    --add-columns '[{"header":"区域","field":"region"}]' \
    --output modified.cpt

# 校验报表
python cpt_tools/validate.py report.cpt
```

## 使用方式三：本地代码引用

在你的 Python 项目中直接 import 使用：

```python
from parsers.cpt_generator import CPTGenerator
from cpt_tools.validate import validate_cpt

# 生成
generator = CPTGenerator()
cpt_content = generator.generate(config_dict)

# 校验
result = validate_cpt("report.cpt")
print(f"通过: {result['valid']}, 检查项: {len(result['checks'])}")
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
