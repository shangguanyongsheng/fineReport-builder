# FineReport 报表构建 Agent V2

基于 AI 的帆软报表自动生成工具，支持多种输入方式生成 .cpt 报表文件。

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [设计文档](docs/设计文档.md) | 系统架构、模块划分、核心流程 |
| [数据模型设计](docs/数据模型设计.md) | 数据源配置、筛选组件配置、JSON 格式 |
| [配置示例文档](docs/配置示例文档.md) | 完整配置示例、常见问题、快速复制模板 |
| [CPT对比分析报告](docs/CPT对比分析报告.md) | 生成报表与原始报表对比分析 |

## 🚀 快速开始

### Web 服务（推荐）

```bash
# 启动 Web 服务
python run.py web --port 5000

# 访问地址
http://localhost:5000
```

### 功能页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 | `/` | 功能概览 |
| **Excel 转 CPT V2** | `/excel-convert-v2` | 🆕 完整配置流程 |
| CPT 分析 | `/cpt-analyze` | 解析现有报表 |
| Class 测试 | `/class-test` | ClassTableData 测试 |

---

## 核心功能

### V2 Excel 转 CPT（推荐）

**5 步向导流程：**

```
Step 1: 上传 Excel 模板 → 自动预览
    ↓
Step 2: 配置数据源（数据库 / Class）
    ↓
Step 3: 配置列映射（Excel 列 → 字段）
    ↓
Step 4: 配置筛选组件（5 对/行）
    ↓
Step 5: 生成 .cpt 报表
```

**支持的数据源：**

| 类型 | 配置项 |
|------|--------|
| **数据库** | 查询名称、SQL、列映射 |
| **Class** | className、返回字段、入参模板 |

**筛选组件：**
- 一行 5 对：说明组件 + 传值组件
- 支持类型：文本框、日期、下拉框、树形下拉等

---

## 命令行模式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python run.py web --port 5000

# 从 Excel 模板构建
python run.py from-excel -f template.xlsx -o report.cpt

# 分析现有报表
python run.py analyze -f report.cpt
```

---

## 项目结构

```
fineReport-builder/
├── docs/                     # 📚 文档目录
│   ├── 设计文档.md
│   ├── 数据模型设计.md
│   ├── 配置示例文档.md
│   └── CPT对比分析报告.md
├── web/                      # Web 服务
│   ├── app.py               # Flask 应用
│   └── templates/           # 页面模板
│       ├── index.html
│       └── excel_convert_v2.html  # V2 页面
├── parsers/                  # 解析器
│   ├── cpt_parser.py
│   ├── cpt_generator.py
│   ├── class_table_data.py
│   └── excel_parser.py
├── agent/                    # Agent 核心
├── examples/                 # 示例文件
├── run.py                    # 主入口
└── README.md
```

---

## 三大核心模块

| 模块 | 说明 | 对应 .cpt 节点 |
|------|------|---------------|
| **数据源** | 数据库/Class 数据集配置 | `TableDataMap` |
| **筛选区域** | 参数面板、筛选组件 | `ReportParameterAttr` |
| **数据展示** | 单元格、数据绑定、样式 | `CellElementList` |

---

## GitHub

https://github.com/shangguanyongsheng/fineReport-builder

## License

MIT