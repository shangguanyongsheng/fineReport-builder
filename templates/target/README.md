# 目标 CPT 目录

用于存放报表生成的目标配置和模板。

---

## 目录结构

```
target/
├── management/          # 管理分析报表目标
│   ├── config.json      # 目标配置
│   └── template.cpt     # 目标模板（带标注）
│
├── detail/              # 明细报表目标
│   ├── config.json
│   └── template.cpt
│
└── custom/              # 自定义报表目标
```

---

## 目标配置说明

目标配置定义了报表的预期结构和校验规则。

### config.json 格式

```json
{
  "name": "管理分析报表",
  "description": "授信合同管理分析报表目标",
  
  "data_source": {
    "type": "ClassTableData",
    "name": "CreditContractDetailData",
    "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
    "required_params": ["orgId", "startDate", "endDate"],
    "optional_params": ["indexInfo", "condition"]
  },
  
  "filter_area": {
    "max_per_row": 5,
    "label_width": 89,
    "input_width": 135,
    "row_gap": 36,
    "supported_types": ["TextEditor", "DateEditor", "ComboBox", "TreeComboBoxEditor"]
  },
  
  "data_area": {
    "header_row": 0,
    "data_row": 1,
    "max_columns": 10
  },
  
  "styles": {
    "header_background": "-16771561",
    "border_color": "-2432266",
    "amount_alignment": "4",
    "amount_format": "#,##0.00"
  }
}
```

---

## 使用方式

### 1. 创建目标配置

```python
# 创建管理分析报表目标
target = {
    "name": "管理分析报表",
    "data_source": {...},
    "filter_area": {...}
}

# 保存到 templates/target/management/config.json
```

### 2. 基于目标生成报表

```python
from agent.core import ReportBuilderAgent

agent = ReportBuilderAgent()
agent.load_target("management")  # 加载目标配置
agent.build_report(
    filter_components=[...],
    data_columns=[...]
)
```

### 3. 校验生成的报表

```python
result = agent.validate_against_target("management")
if result['valid']:
    print("✅ 符合目标规范")
else:
    print("❌ 不符合:", result['issues'])
```

---

_📅 创建日期：2026-04-09_