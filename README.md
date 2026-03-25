# FineReport 报表构建 Agent

基于 AI 的帆软报表自动生成工具，通过自然语言描述生成 .cpt 报表文件。

## 核心功能

### 三大核心模块

| 模块 | 说明 | 对应 .cpt 节点 |
|------|------|---------------|
| **数据源** | 定义数据集、SQL查询、参数 | `TableDataMap` |
| **筛选区域** | 参数面板 UI 控件 | `ReportParameterAttr` |
| **数据展示区** | 报表单元格、数据绑定、样式 | `Report/CellElementList` |

## 项目结构

```
fineReport-builder/
├── agent/                    # Agent 核心
│   ├── __init__.py
│   ├── requirement_parser.py # 需求解析器
│   ├── sql_generator.py      # SQL 生成器
│   └── report_builder.py     # 报表构建器
├── templates/                # 模板
│   ├── datasource.xml        # 数据源模板
│   ├── parameter.xml         # 参数面板模板
│   └── report.xml            # 报表模板
├── parsers/                  # 解析器
│   ├── cpt_parser.py         # .cpt 文件解析
│   └── cpt_generator.py      # .cpt 文件生成
├── gui/                      # GUI 界面
│   └── main_window.py
├── config/                   # 配置
│   └── config.yaml
├── examples/                 # 示例
│   └── FinanceCreditContractAnalysis.cpt
├── run.py                    # 主入口
└── README.md
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 GUI
python run.py

# 或命令行
python run.py --input "创建销售报表，按区域分组，显示金额、数量"
```

## 使用示例

### 输入（自然语言）

```
创建一个销售统计报表：
- 数据源：sales 数据库
- 筛选条件：日期范围、区域、产品类型
- 展示：按区域分组，显示销售额、数量、占比
- 支持折算币种
```

### 输出

1. **数据源配置** (SQL + 参数)
2. **筛选面板** (日期选择器、下拉框、树形选择器)
3. **报表模板** (.cpt 文件)
4. **预览说明**

## 核心设计

### 数据源模块 (TableDataMap)

```xml
<TableData name="sales_data" class="com.fr.data.impl.DBTableData">
    <Parameters>
        <Parameter><Attributes name="startDate"/></Parameter>
        <Parameter><Attributes name="endDate"/></Parameter>
        <Parameter><Attributes name="region"/></Parameter>
    </Parameters>
    <Connection class="com.fr.data.impl.NameDatabaseConnection">
        <DatabaseName><![CDATA[sales_db]]></DatabaseName>
    </Connection>
    <Query><![CDATA[SELECT * FROM sales WHERE date >= '${startDate}' AND date <= '${endDate}']]></Query>
</TableData>
```

### 筛选区域模块 (ReportParameterAttr)

支持的控件类型：
- `TextEditor` - 文本输入
- `DateEditor` - 日期选择
- `ComboBox` - 下拉单选
- `ComboCheckBox` - 下拉多选
- `TreeComboBoxEditor` - 树形选择

### 数据展示区模块 (Report)

```xml
<CellElementList>
    <C c="0" r="0">  <!-- 第0列 第0行 -->
        <O><![CDATA[区域]]></O>  <!-- 单元格内容 -->
    </C>
    <C c="0" r="1">
        <O t="DSColumn">  <!-- 数据绑定 -->
            <Attributes dsName="sales_data" columnName="region"/>
        </O>
        <Expand dir="0"/>  <!-- 纵向扩展 -->
    </C>
</CellElementList>
```

## 工作流程

```
用户输入 (自然语言)
      │
      ▼
┌──────────────────┐
│  需求解析器       │ → 提取：数据源、筛选条件、展示需求
└──────────────────┘
      │
      ▼
┌──────────────────┐
│  SQL 生成器       │ → 生成：数据集 SQL、参数定义
└──────────────────┘
      │
      ▼
┌──────────────────┐
│  控件映射器       │ → 生成：筛选面板控件配置
└──────────────────┘
      │
      ▼
┌──────────────────┐
│  报表构建器       │ → 生成：单元格布局、数据绑定、样式
└──────────────────┘
      │
      ▼
  .cpt 文件输出
```

## License

MIT