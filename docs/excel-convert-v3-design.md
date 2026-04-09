# Excel-Convert-V3 设计文档

## 概述

Excel-Convert-V3 是帆软报表生成器的 Web 界面，提供可视化配置界面，帮助用户快速生成 FineReport .cpt 报表文件。

## 访问地址

```
http://localhost:5002/excel-convert-v3
```

---

## 功能模块

### Step 1: 基本信息

| 字段 | 说明 | 默认值 |
|------|------|--------|
| 报表标题 | 生成报表的标题 | 新建报表 |
| Sheet名称 | 工作表名称 | Sheet1 |
| Excel模板 | 可选，上传Excel自动解析表头 | - |

---

### Step 2: 数据源配置

支持两种数据源类型：

#### 2.1 数据库类型 (database)

| 字段 | 说明 |
|------|------|
| 数据源名称 | 唯一标识，如 `main_data` |
| 数据库连接 | 数据库名称，如 `cfs-report` |
| SQL语句 | 查询语句，参数用 `${paramName}` 占位 |

#### 2.2 Class 类型 (class)

| 字段 | 格式 | 说明 |
|------|------|------|
| 数据源名称 | 字符串 | 唯一标识 |
| 类名 | 字符串 | 如 `com.yocyl.fr.engine.tableData.finance.GuaranteeContractDetailData` |
| **返回字段（出参）** | 字符串数组 | `["tenantId", "guaranteeDebtorId", "guaranteeDebtorName"]` |
| **入参模板** | 对象数组 | `[{"orgId": ""}, {"startDate": ""}, {"indexInfo": {...}}]` |

**入参模板规则：**
- 每个对象只有一个 key
- 空值 `""` 表示从筛选组件获取
- 有值表示写死默认值（复杂 JSON 会自动转字符串）

**示例：**
```json
{
  "name": "GuaranteeContractDetailData",
  "type": "class",
  "class_name": "com.yocyl.fr.engine.tableData.finance.GuaranteeContractDetailData",
  "return_fields": ["tenantId", "guaranteeDebtorId", "amount", "startDate", "endDate"],
  "parameter_template": [
    {"orgId": ""},
    {"startDate": ""},
    {"endDate": ""},
    {"indexInfo": [{"fieldCode": "repay.id", "alias": "id"}]}
  ]
}
```

---

### Step 3: 列映射配置

支持**表单模式**和**JSON模式**两种输入方式。

**表单模式**：每列配置表头（中文）和字段名（英文）

**JSON模式**：
```json
{
  "A": {"header": "序号", "field": "tenantId"},
  "B": {"header": "担保人", "field": "guaranteeDebtorName"},
  "C": {"header": "金额", "field": "amount"}
}
```

---

### Step 4: 筛选组件配置

**一行五列布局，每行通过JSON输入：**

```json
[
  {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
  {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
  {"label": "组织", "code": "orgId", "type": "TreeComboBoxEditor"},
  {"label": "区域", "code": "region", "type": "ComboBox"},
  {"label": "状态", "code": "status", "type": "ComboBox"}
]
```

**支持的控件类型：**
- `TextEditor` - 文本框
- `DateEditor` - 日期选择
- `ComboBox` - 下拉框
- `TreeComboBoxEditor` - 树形下拉
- `NumberEditor` - 数字输入

**布局规范：**
| 参数 | 值 |
|------|-----|
| Label 宽度 | 89px |
| 输入框宽度 | 135px |
| 控件高度 | 28px |
| Label与输入框间距 | 4px |
| 行间距 | 8px |

---

### Step 5: 样式配置

**固定样式规范：**

| 属性 | RGB值 | 十进制值 |
|------|-------|----------|
| 表头背景色 | (233, 233, 255) | -16771561 |
| 表头边框色 | (218, 226, 246) | -2432266 |

---

## API 接口

### POST /api/v2/generate

**请求体：**
```json
{
  "datasource": {
    "name": "string",
    "type": "class | database",
    "class_name": "string (class类型)",
    "return_fields": ["field1", "field2"],
    "parameter_template": [{"param1": ""}]
  },
  "column_mapping": {
    "A": {"header": "表头", "field": "fieldName"}
  },
  "filter_components": [
    {"label": "开始日期", "code": "startDate", "type": "DateEditor"}
  ],
  "styles": [],
  "report": {
    "title": "报表标题",
    "sheet_name": "Sheet1"
  }
}
```

**响应：**
```json
{
  "success": true,
  "output_file": "report_20260409.cpt",
  "download_url": "/api/download/report_20260409.cpt",
  "config": { /* 生成的配置 */ }
}
```

---

## 文件结构

```
fineReport-builder/
├── web/
│   ├── app.py                    # Flask 主应用
│   ├── templates/
│   │   └── excel_convert_v3.html  # 前端页面
│   └── static/
├── parsers/
│   ├── cpt_generator.py          # CPT 生成器（核心）
│   ├── cpt_parser.py             # CPT 解析器
│   └── class_table_data.py       # ClassTableData 处理
├── outputs/                       # 生成的 CPT 文件
├── uploads/                       # 上传的 Excel 文件
└── docs/
    └── excel-convert-v3-design.md # 本文档
```

---

## 关键代码位置

### 1. 筛选组件布局参数

文件：`parsers/cpt_generator.py`

```python
# ===== 筛选组件布局规范 =====
LABEL_WIDTH = 89      # Label 控件宽度
INPUT_WIDTH = 135     # 输入控件宽度
LABEL_INPUT_GAP = 4   # Label 与输入框横向间距
ROW_GAP = 8           # 行间距
ROW_HEIGHT = 28       # 控件高度
PAIRS_PER_ROW = 5     # 每行组件对数
```

### 2. 样式配置

文件：`parsers/cpt_generator.py` → `_get_default_styles()`

```python
{
    "name": "表头",
    "background": "-16771561",  # RGB(233, 233, 255)
    "border": True
}
# 边框颜色：-2432266  # RGB(218, 226, 246)
```

### 3. 前端数据收集

文件：`web/templates/excel_convert_v3.html` → `collectConfig()`

---

## 更新日志

### 2026-04-09

- 修复 Class 数据源入参/出参格式
  - 入参：对象数组 `[{"param": ""}]`
  - 出参：字符串数组 `["field1", "field2"]`
- 优化列映射配置，支持表头+字段分离
- 优化筛选组件配置，一行五列布局
- 更新样式规范
  - 表头背景色：RGB(233, 233, 255) → -16771561
  - 表头边框色：RGB(218, 226, 246) → -2432266
  - Label 宽度：89px
  - 输入框宽度：135px
  - Label与输入框间距：4px
  - 行间距：8px

---

## 注意事项

1. **Flask 缓存**：开发模式使用 `--debug` 参数禁用模板缓存
2. **列数限制**：最多支持 18 列（A-R）
3. **筛选组件限制**：最多支持 10 个（2行×5列）
4. **金额字段自动识别**：字段名包含 `amount`、`money`、`金额`、`price`、`费用` 的自动右对齐