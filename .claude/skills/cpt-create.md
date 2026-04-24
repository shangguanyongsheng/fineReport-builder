name: cpt-create
description: 根据用户输入创建全新的 CPT 报表文件。支持 class 和 database 两种数据源类型。基于模板增量修改，避免全量生成 XML 导致遗漏隐属性。
type: tool

---

# CPT 创建技能（增量模式）

## 触发条件

用户要求创建一个新的报表（无论输入多么模糊），**必须**先进行需求结构化。

## 执行流程

### Step 1: 需求结构化（强制）

**不管用户输入了什么内容，必须先输出以下结构化配置，再执行后续步骤。** 结构化时，用户提到的细节必须写进去，没提到的不实现、不猜测。

结构化的配置必须完整包含以下所有字段：

```json
{
    "title": "报表标题",
    "template_type": "detail",
    "data_sources": [
        {
            "name": "数据源名称",
            "type": "ClassTableData",
            "class_name": "com.xxx.DataClass",
            "parameters": [
                {"name": "param1", "default": ""}
            ]
        }
    ],
    "sql_data_sources": [
        {
            "name": "字典数据源名",
            "type": "DBTableData",
            "sql_template": "finance/biz_dict/credit_product_code",
            "database": "cfs-report",
            "tenant_param": "fine_username9",
            "parameters": [{"name": "fine_username9", "default": ""}]
        }
    ],
    "tree_data_sources": [
        {
            "tree_name": "Tree1",
            "base_data_source": "organization",
            "mark_field_index": 1,
            "parent_mark_field_index": 3,
            "mark_field_name": "id",
            "parent_mark_field_name": "parent_id"
        }
    ],
    "filter_controls": [
        {
            "label": "显示名称",
            "code": "paramCode",
            "type": "TextEditor"
        }
    ],
    "cells": [
        {
            "column": 0,
            "row": 0,
            "value": "表头",
            "style_index": 1
        }
    ]
}
```

#### 结构化字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | 是 | 报表标题，用户没说就用描述推断 |
| `template_type` | 是 | `"detail"` 明细 / `"manager"` 管理分析 / `"自定义"` |
| `data_sources` | 是 | ClassTableData 数据源列表 |
| `data_sources[].name` | 是 | 数据源名称 |
| `data_sources[].type` | 是 | `"ClassTableData"` |
| `data_sources[].class_name` | type=ClassTableData 时必填 | Java 类全路径 |
| `data_sources[].parameters` | 是 | 参数列表，空值=从筛选组件获取 |
| `data_sources[].parameters[].name` | 是 | 参数名 |
| `data_sources[].parameters[].default` | 是 | 默认值，空字符串 `""` 表示动态获取 |
| `sql_data_sources` | 否 | SQL 数据源（字典查询） |
| `sql_data_sources[].sql_template` | 否 | 模板路径，如 `finance/biz_dict/credit_product_code` |
| `sql_data_sources[].database` | sql_data_sources 存在时必填 | 数据库名 |
| `tree_data_sources` | 否 | 树形数据源（RecursionTableData） |
| `tree_data_sources[].tree_name` | 树存在时必填 | 树节点名称 |
| `tree_data_sources[].base_data_source` | 树存在时必填 | 底层 DBTableData 名称 |
| `tree_data_sources[].mark_field_index` | 树存在时必填 | 节点 ID 列索引 |
| `tree_data_sources[].parent_mark_field_index` | 树存在时必填 | 父节点 ID 列索引 |
| `tree_data_sources[].mark_field_name` | 否 | 节点 ID 字段名，默认 `id` |
| `tree_data_sources[].parent_mark_field_name` | 否 | 父节点 ID 字段名，默认 `parent_id` |
| `filter_controls` | 是 | 筛选组件列表 |
| `filter_controls[].label` | 是 | 显示名称 |
| `filter_controls[].code` | 是 | 参数 code，必须与 data_sources 中参数名对应 |
| `filter_controls[].type` | 是 | `TextEditor` / `DateEditor` / `ComboBox` / `TreeComboBoxEditor` |
| `filter_controls[].dict_data_source` | type=ComboBox/TreeComboBoxEditor 时必填 | 绑定的数据源名称 |
| `filter_controls[].dict_ki` | 否 | 字典 key 字段，默认 `dict_key` |
| `filter_controls[].dict_vi` | 否 | 字典 value 字段，默认 `dict_value` |
| `filter_controls[].muti_select` | 否 | TreeComboBoxEditor 是否多选，默认 `false` |
| `filter_controls[].select_leaf_only` | 否 | TreeComboBoxEditor 是否只选叶子，默认 `false` |
| ~~`filter_controls[].action_buttons`~~ | ~~否~~ | ~~**已废弃**：查询和重置按钮自动生成，无需配置~~ |
| `cells` | 是 | 单元格列表 |
| `cells[].column` | 是 | 列索引 |
| `cells[].row` | 是 | 行索引，0=表头行，1=数据行 |
| `cells[].value` | 是 | 表头文本或公式 |
| `cells[].value_type` | row>=1 时必填 | `"DSColumn"` / `"Formula"` / `"Static"` |
| `cells[].data_source` | value_type=DSColumn 时必填 | 数据源名称 |
| `cells[].column_name` | value_type=DSColumn 时必填 | 字段名 |
| `cells[].expand_dir` | value_type=DSColumn 时必填 | 展开方向，通常 `0` |
| `cells[].style_index` | 是 | 样式索引 |

#### 结构化规则

1. **用户提到的每个细节都必须写入结构化配置**，不要遗漏
2. **用户没提到的字段不要自行添加或假设**
3. **结构化配置必须先输出给用户确认**，确认后再进入 Step 2
4. 如果用户输入模糊，结构化前先询问缺失的必要字段

### Step 2: 校验

1. **数据源参数完整性**：每个空值参数都有对应筛选组件
2. **展示列字段完整性**：非序号列必须有字段名
3. **样式引用检查**：cells 中的 style_index 不超出范围

### Step 3: 调用增量生成器

基于模板修改 3 个关键区域，保留所有隐属性：

```python
import sys
sys.path.insert(0, '/home/admin/python-works/fineReport-builder')
from parsers.incremental_generator import IncrementalCPTGenerator

generator = IncrementalCPTGenerator(template_type=config.get('template_type', 'detail'))
output_path = generator.generate(config)
```

**工作原理：**

```
1. 加载模板（detail 或 manager）
2. 替换 TableDataMap      ← 数据源定义（含 DBTableData + RecursionTableData）
3. 替换 CellElementList    ← 单元格列表
4. 替换 ReportParameterAttr/Layout  ← 筛选组件
5. 保留其余所有节点：
   ReportWebAttr, StyleList, DesignerVersion,
   PreviewType, ForkIdAttrMark, TemplateThemeAttrMark...
```

### Step 4: 输出确认

```
✅ 报表创建成功: outputs/xxx.cpt
📊 数据源: 1 个 (ClassTableData)
🔍 筛选组件: 3 对
📋 展示列: 5 列
```

## 筛选组件布局自动计算

```
给定 N 个筛选组件，自动计算位置：

LABEL_WIDTH = 89
INPUT_WIDTH = 135
LABEL_INPUT_GAP = 4
PAIR_GAP = 4
ROW_HEIGHT = 28
ROW_GAP = 8
PAIRS_PER_ROW = 5
START_X = 10
START_Y = 10

for i in range(N):
    row = i // PAIRS_PER_ROW
    col = i % PAIRS_PER_ROW
    pair_width = LABEL_WIDTH + LABEL_INPUT_GAP + INPUT_WIDTH  # 228
    x_label = START_X + col * (pair_width + PAIR_GAP)
    x_input = x_label + LABEL_WIDTH + LABEL_INPUT_GAP
    y = START_Y + row * (ROW_HEIGHT + ROW_GAP)
```

## 查询和重置按钮（强制）

**每个报表必须固定包含查询和重置按钮**，按钮会自动添加在筛选面板末尾，无需在配置中指定：

| 按钮 | 控件名 | 类型 | 快捷键 | 说明 |
|------|--------|------|--------|------|
| 查询 | `Search` | `FormSubmitButton` | Enter | 提交表单刷新数据 |
| 重置 | `Reload` | `FormSubmitButton` | Enter | 清空所有筛选条件 |

按钮位置：放在所有筛选组件行的下一行右侧。

## SQL 数据源（字典查询）

当筛选组件需要下拉字典值时，使用 SQL 数据源从业务字典表查询。

### 业务字典（带租户隔离）

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

`sql_template` 会自动从 `templates/base_sql_templates/finance/biz_dict/credit_product_code.sql` 加载。

### 通用系统字典（无租户隔离）

```json
{
  "name": "currency",
  "type": "DBTableData",
  "sql": "select concat(id,'') as id,code,dict_key,dict_value from sys_dict where code = 'currency' and is_deleted = 0",
  "database": "cfs-report",
  "parameters": []
}
```

### 模板目录

```
templates/base_sql_templates/
├── _common/
│   ├── sys_dict.sql          # 系统字典（无租户）
│   └── sys_dict_biz.sql      # 业务字典（含租户隔离）
├── finance/
│   └── biz_dict/
│       └── credit_product_code.sql  # 增信方式
└── ticket/
    └── biz_dict/              # 票据域（预留）
```

新增字典模板：在对应域目录下创建 `.sql` 文件，在 `_template.md` 中登记。

### 控件绑定字典数据源

下拉控件（ComboBox/TreeComboBoxEditor）通过 Dictionary 节点绑定：

```xml
<Dictionary class="com.fr.data.impl.TableDataDictionary">
  <FormulaDictAttr kiName="dict_key" viName="dict_value"/>
  <TableDataDictAttr>
    <TableData class="com.fr.data.impl.NameTableData">
      <Name><![CDATA[数据源名称]]></Name>
    </TableData>
  </TableDataDictAttr>
</Dictionary>
```

## 数据列自动生成规则

1. **序号列**：如果第一个列名为"序号"且字段为空 → 使用 `seq()` 公式
2. **金额字段**：字段名包含 amount/money/金额/price/费用 → 使用金额样式（索引 3）
3. **普通字段**：使用数据样式（索引 2）
4. **表头**：使用表头样式（索引 1），第一列用索引 0

## 示例：从用户对话到完整配置

**用户输入**：
> 创建一个授信明细报表
> 数据源：com.yocyl.fr.engine.tableData.finance.CreditContractDetailData，名称 CreditData
> 入参：startDate(空)、endDate(空)、orgId(空)
> 筛选：开始日期(DateEditor)、结束日期(DateEditor)、组织机构(TreeComboBoxEditor)
> 展示列：序号、合同编号(contractNo)、合同名称(contractName)、金额(amount)

**结构化配置**：
```json
{
  "title": "授信明细报表",
  "template_type": "detail",
  "data_sources": [{
    "name": "CreditData",
    "type": "ClassTableData",
    "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
    "parameters": [
      {"name": "startDate", "default": ""},
      {"name": "endDate", "default": ""},
      {"name": "orgId", "default": ""}
    ]
  }],
  "filter_controls": [
    {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
    {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
    {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"}
  ],
  "cells": [
    {"column": 0, "row": 0, "value": "序号", "style_index": 0},
    {"column": 1, "row": 0, "value": "合同编号", "style_index": 1},
    {"column": 2, "row": 0, "value": "合同名称", "style_index": 1},
    {"column": 3, "row": 0, "value": "金额", "style_index": 1},
    {"column": 0, "row": 1, "value_type": "Formula", "value": "seq()", "style_index": 2},
    {"column": 1, "row": 1, "value_type": "DSColumn", "data_source": "CreditData", "column_name": "contractNo", "expand_dir": 0, "style_index": 2},
    {"column": 2, "row": 1, "value_type": "DSColumn", "data_source": "CreditData", "column_name": "contractName", "expand_dir": 0, "style_index": 2},
    {"column": 3, "row": 1, "value_type": "DSColumn", "data_source": "CreditData", "column_name": "amount", "expand_dir": 0, "style_index": 3}
  ]
}
```
