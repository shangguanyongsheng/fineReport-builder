name: cpt-create
description: 根据用户输入创建全新的 CPT 报表文件。支持 class 和 database 两种数据源类型。基于模板增量修改，避免全量生成 XML 导致遗漏隐属性。
type: tool

---

# CPT 创建技能（增量模式）

## 触发条件

用户要求创建一个新的报表，并且：
- 提供了数据源信息（名称、类型、class 路径）
- 提供了筛选条件（中文名称 + 英文 code）
- 提供了展示列（中文表头 + 英文字段名）

## 执行流程

### Step 1: 需求结构化

将用户输入解析为标准配置结构：

```python
config = {
    "title": "报表标题",
    "template_type": "detail",        # "detail" 或 "manager"
    "data_sources": [
        {
            "name": "数据源名称",
            "type": "ClassTableData",  # 或 DBTableData
            "class_name": "com.xxx.DataClass",  # class 类型必需
            "parameters": [
                {"name": "orgId", "default": ""},      # 空 → 筛选组件
                {"name": "fixedParam", "default": "123"}  # 有值 → 固定
            ]
        }
    ],
    "filter_controls": [
        {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
        {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"},
    ],
    "cells": [
        # 表头行 (row=0)
        {"column": 0, "row": 0, "value": "合同编号", "style_index": 1},
        # 数据行 (row=1)
        {"column": 0, "row": 1, "value_type": "DSColumn",
         "data_source": "数据源名称", "column_name": "contractNo",
         "expand_dir": 0, "style_index": 2}
    ],
}
```

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
2. 替换 TableDataMap      ← 数据源定义
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

**解析后配置**：
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
