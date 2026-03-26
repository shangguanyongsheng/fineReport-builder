# FineReport 报表构建 Agent

基于 AI 的帆软报表自动生成工具，支持多种输入方式生成 .cpt 报表文件。

## 核心功能

### 多种输入方式

| 输入方式 | 命令 | 说明 |
|---------|------|------|
| 🗣️ 自然语言 | `build -i "..."` | AI 解析需求，自动生成报表 |
| 📊 Excel 模板 | `from-excel -f template.xlsx` | 从 Excel 布局生成 .cpt |
| 📄 .cpt 分析 | `analyze -f report.cpt` | 分析现有报表结构 |
| 🔧 ClassTableData | `interactive -f report.cpt` | 生成交互式测试页面 |

### 三大核心模块

| 模块 | 说明 | 对应 .cpt 节点 |
|------|------|---------------|
| **数据源** | 定义数据集、SQL查询、参数、Java类 | `TableDataMap` |
| **筛选区域** | 参数面板 UI 控件 | `ReportParameterAttr` |
| **数据展示区** | 报表单元格、数据绑定、样式 | `Report/CellElementList` |

## 项目结构

```
fineReport-builder/
├── agent/                    # Agent 核心
│   ├── __init__.py
│   ├── requirement_parser.py # 需求解析器
│   └── report_builder.py     # 报表构建器
├── parsers/                  # 解析器
│   ├── cpt_parser.py         # .cpt 文件解析
│   ├── cpt_generator.py      # .cpt 文件生成
│   ├── class_table_data.py   # ClassTableData 解析 + 交互测试
│   └── excel_parser.py       # Excel 文件解析 + 预览
├── gui/                      # GUI 界面
│   └── main_window.py
├── config/                   # 配置
│   └── config.yaml
├── examples/                 # 示例文件
│   ├── FinanceCreditContractAnalysis.cpt
│   └── FinanceCreditContractAnalysis_interactive.html
├── run.py                    # 主入口
└── README.md
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 查看帮助
python run.py --help

# 从自然语言构建报表
python run.py build -i "创建销售报表，按区域分组，显示金额、数量"

# 从 Excel 模板构建
python run.py from-excel -f template.xlsx -o report.cpt

# 分析现有报表
python run.py analyze -f report.cpt

# Excel 预览（浏览器交互）
python run.py excel-preview -f template.xlsx -o

# ClassTableData 交互测试
python run.py serve -f report.cpt -o
```

## 命令详解

### 1. build - 构建报表

从自然语言或配置文件构建 .cpt 报表：

```bash
# 自然语言输入
python run.py build -i "创建销售报表，按区域分组，显示金额、数量" -o sales.cpt

# 配置文件输入
python run.py build -c config.json -o output.cpt
```

### 2. from-excel - 从 Excel 构建

将 Excel 模板转换为 .cpt 格式：
- 单元格布局 → CellElementList
- Excel 样式 → StyleList
- 合并单元格 → rowspan/colspan

```bash
python run.py from-excel -f template.xlsx \
    --sheet 0 \
    --ds-name "sales_data" \
    --database "cfs-report" \
    -o report.cpt
```

### 3. excel-preview - Excel 预览

在浏览器中预览 Excel 并配置转换参数：

```bash
python run.py excel-preview -f template.xlsx --port 18081 -o
```

### 4. analyze - 分析报表

解析 .cpt 文件结构：

```bash
python run.py analyze -f report.cpt
```

输出：
- 数据源列表（DBTableData、ClassTableData）
- 参数面板控件
- 单元格布局统计

### 5. interactive - ClassTableData 测试

为 ClassTableData 数据集生成交互式测试页面：

```bash
# 生成 HTML
python run.py interactive -f report.cpt -o test.html

# 启动测试服务器
python run.py serve -f report.cpt --port 18080 -o
```

浏览器界面功能：
- 填写参数值
- 配置 API 端点
- 发送测试请求
- 查看请求/响应

## ClassTableData 支持

### 解析能力

自动提取：
- 类名（className）
- 参数定义（name、default、type）
- 参数类型推断（string/number/date/array/object）

### 发现的数据集类型

| 类名 | 说明 |
|------|------|
| CreditContractDetailData | 授信明细数据 |
| CreditContractStatisticData | 授信统计数据 |
| CreditContractUserOrgStatisticData | 用信单位统计 |
| CreditProductStatisticData | 授信产品统计 |

## Excel → .cpt 转换

### 映射关系

| Excel | .cpt |
|-------|------|
| 单元格 (A1) | `<C c="0" r="0">` |
| 合并单元格 | `rowspan` / `colspan` |
| 字体样式 | `<Style><FRFont>` |
| 背景色 | `<Background>` |
| 对齐方式 | `<Alignment>` |
| 公式 | `<O t="Formula">` |

### 转换示例

```python
from parsers.excel_parser import ExcelParser

parser = ExcelParser()
structure = parser.parse('template.xlsx')

# 转换单元格
cells = parser.to_cpt_cells(structure.sheets[0])

# 转换样式
styles = parser.to_cpt_styles(structure.sheets[0].styles)
```

## 工作流程

```
用户输入
  ├─ 自然语言 ──→ AI 解析 ──→ SQL + 控件配置 ──┐
  ├─ Excel 模板 ──→ 布局解析 ──→ 单元格结构 ──┤
  └─ 配置文件 ──→ JSON 解析 ─────────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │ CPT Generator │
                                        └──────────────┘
                                                │
                                                ▼
                                         .cpt 文件输出
```

## License

MIT