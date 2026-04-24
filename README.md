# FineReport Builder — Claude Code Skills for 帆软报表开发

将帆软报表开发经验沉淀为可复用的 **Claude Code Skills**，复制到任意项目即可直接使用。

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Code                          │
│                                                             │
│  ┌───────────────────┐   ┌───────────────────┐              │
│  │   /cpt-knowledge  │   │   用户对话        │              │
│  │   (知识库)        │   │   (描述需求)      │              │
│  └────────┬──────────┘   └─────────┬─────────┘              │
│           │                        │                        │
│  ┌────────▼────────────────────────▼─────────┐             │
│  │            .claude/skills/                 │             │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐  │             │
│  │  │cpt-create│ │cpt-modify│ │cpt-validate│  │             │
│  │  └────┬─────┘ └────┬─────┘ └─────┬─────┘  │             │
│  └───────┼────────────┼─────────────┼────────┘             │
│          │            │             │                      │
│          ▼            ▼             ▼                      │
│  ┌───────────────────────────────────────────┐             │
│  │            parsers/                        │             │
│  │                                            │             │
│  │  incremental_generator.py                  │             │
│  │  cpt_generator.py                          │             │
│  │  cpt_parser.py                             │             │
│  │  class_table_data.py                       │             │
│  └──────┬────────────────────────────────────┘             │
│         │                                                  │
│         ▼                                                  │
│  ┌───────────────────┐                                    │
│  │   templates/      │                                    │
│  │  detail/*.cpt     │  ← 基础模板（保留全部隐属性）       │
│  │  manager/*.cpt    │                                    │
│  │  base_sql_templates/ │ ← SQL 模板（按业务域组织）       │
│  └───────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  outputs/*.cpt       │  ← 生成的帆软报表文件
  └──────────────────────┘
```

## 核心工作原理

`cpt-create` 和 `cpt-modify` 采用 **增量模板修改** 模式，避免全量生成 XML：

```
1. 加载模板（detail 或 manager）
2. 替换 TableDataMap       ← 数据源定义
3. 替换 CellElementList     ← 单元格列表
4. 替换 ReportParameterAttr ← 筛选组件
5. 保留其余所有节点：
   ReportWebAttr, StyleList, DesignerVersion,
   PreviewType, ForkIdAttrMark, TemplateThemeAttrMark...
```

只改动 3 个关键区域，保留所有帆软隐属性，确保设计器打开无兼容问题。

## 使用方式

**下载项目到本地 → 在该项目下打开 Claude Code → 直接对话开发**

无需安装依赖，无需启动服务。Claude Code 会自动加载 `.claude/skills/` 中的技能定义。

```bash
# 1. 下载项目
git clone https://github.com/shangguanyongsheng/fineReport-builder.git
cd fineReport-builder

# 2. 复制 skills 到你的业务项目（可选）
cp -r .claude/skills/ 你的项目/.claude/

# 3. 在 Claude Code 中直接对话，描述报表需求即可
```

## 内置 Skills

| Skill | 类型 | 用途 |
|-------|------|------|
| `/cpt-knowledge` | reference | 加载 CPT 知识库（XML 结构、控件类型、样式系统） |
| `/cpt-create` | tool | 从零创建全新的 .cpt 报表文件 |
| `/cpt-modify` | tool | 基于现有 .cpt 模板增删筛选组件、数据列、参数 |
| `/cpt-validate` | tool | 验证 .cpt 文件是否符合帆软规范 |

### 创建新报表流程

```
/cpt-knowledge          ← 加载知识库
描述你的需求              ← 数据源、筛选条件、展示列
/cpt-create             ← 生成 .cpt 文件
/cpt-validate           ← 验证规范
```

### 修改现有报表流程

```
/cpt-knowledge          ← 加载知识库
描述修改内容              ← 新增/删除什么组件或列
/cpt-modify             ← 修改 .cpt 文件
/cpt-validate           ← 验证规范
```

## 项目结构

| 目录 | 定位 | 说明 |
|------|------|------|
| `.claude/skills/` | **核心交付物** | 可复制到其他项目的 Skills 包 |
| `cpt_tools/` | 命令行工具 | 生成、校验，可独立使用或被 Skills 调用 |
| `parsers/` | 解析器库 | 增量生成器、CPT 解析、ClassTableData、SQL 数据源生成 |
| `templates/` | 基础模板 | `detail/` 明细报表、`manager/` 管理分析报表、`base_sql_templates/` SQL 模板 |
| `web/` | 测试工具 | 验证 Skills 生成的 CPT 是否正确，非交付物 |

## 命令行工具（可选）

不通过对话，直接通过命令行生成和校验：

```bash
# 通过 JSON 配置生成报表（增量模式）
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

## 本地代码引用（可选）

```python
from parsers.incremental_generator import IncrementalCPTGenerator
from cpt_tools.validate import validate_cpt

# 基于模板增量生成
generator = IncrementalCPTGenerator(template_type='detail')
path = generator.generate(config)

# 校验
result = validate_cpt("report.cpt")
```

## 核心约束

- **数据源参数只能多不能少**：筛选组件必须覆盖所有空值参数
- **ClassTableData 必须有 `<Parameters>` 节点**
- **`<O>` 标签必须用 CDATA 格式**：`<O><![CDATA[value]]></O>`
- **样式索引必须在 StyleList 范围内**
- **筛选组件布局**：每行 5 对（Label 89px + Input 135px），间距 4px，行间距 8px

## SQL 数据源模板

筛选项需要下拉字典值时，使用 SQL 数据源从 `sys_dict` 或 `sys_dict_biz` 查询：

```json
{
  "name": "creditProductCode",
  "type": "DBTableData",
  "sql_template": "finance/biz_dict/credit_product_code",
  "database": "cfs-report",
  "tenant_param": "fine_username9",
  "parameters": [{"name": "fine_username9", "default": ""}]
}
```

SQL 模板按业务域组织：

```
templates/base_sql_templates/
├── _common/              # sys_dict, sys_dict_biz 通用模板
├── finance/biz_dict/     # 财务业务字典（增信方式等）
└── ticket/biz_dict/      # 票据业务字典（预留）
```

- 模板中使用 `${fine_username9}` 帆软运行时变量，不被替换为字面量
- 新增模板：在对应域目录创建 `.sql` 文件，在 `_template.md` 中登记
- 下拉控件通过 `Dictionary` 节点绑定数据源（`kiName="dict_key"`, `viName="dict_value"`）
- 也可直接在代码中使用 `SqlDataSourceGenerator`：

```python
from parsers.sql_data_source import SqlDataSourceGenerator

gen = SqlDataSourceGenerator()

# 业务字典（带租户隔离）
ds = gen.generate_biz_dict('creditProductCode', 'finance_loan_product', 'cfs-report')

# 系统字典（无租户隔离）
ds = gen.generate_sys_dict('currency', 'currency', 'cfs-report')

# 从模板文件加载
ds = gen.from_template_file('creditProductCode',
    'finance/biz_dict/credit_product_code.sql', 'cfs-report',
    variables={'tenant_param': 'fine_username9'})
```

## License

MIT
