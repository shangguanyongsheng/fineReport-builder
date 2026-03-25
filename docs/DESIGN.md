# FineReport 报表构建 Agent 设计文档

## 一、项目概述

基于 AI 的帆软报表自动生成工具，通过自然语言描述生成 `.cpt` 报表文件。

### 核心目标

解决帆软报表开发中的痛点：
- 手动拖拉拽组件费时费力
- 数据源配置重复繁琐
- 字段绑定容易出错

---

## 二、帆软 .cpt 文件结构分析

### 2.1 三大核心模块

```
┌─────────────────────────────────────────────────────────────────┐
│  WorkBook (根节点)                                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. TableDataMap (数据源映射)                               │  │
│  │    - 数据集定义                                           │  │
│  │    - SQL 查询                                             │  │
│  │    - 参数定义                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2. ReportParameterAttr (筛选区域/参数面板)                 │  │
│  │    - 参数控件 (下拉框、日期选择、树形选择等)                │  │
│  │    - 控件布局                                             │  │
│  │    - 数据字典                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. Report (数据展示区)                                     │  │
│  │    - CellElementList (单元格列表)                          │  │
│  │    - 数据绑定                                             │  │
│  │    - 样式定义                                             │  │
│  │    - 公式                                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  └─ StyleList (样式列表)                                        │
│  └─ ReportWebAttr (Web属性)                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据源模块 (TableDataMap)

#### 数据集类型

| 类型 | 类名 | 说明 |
|------|------|------|
| **数据库查询** | `DBTableData` | 直接执行 SQL 查询 |
| **程序数据集** | `ClassTableData` | 调用 Java 类获取数据 |
| **树形数据集** | `RecursionTableData` | 递归构建树形结构 |

#### XML 结构示例

```xml
<TableData name="sales_data" class="com.fr.data.impl.DBTableData">
    <!-- 参数定义 -->
    <Parameters>
        <Parameter>
            <Attributes name="startDate"/>
            <O><![CDATA[]]></O>
        </Parameter>
        <Parameter>
            <Attributes name="region"/>
            <O><![CDATA[]]></O>
        </Parameter>
    </Parameters>
    
    <!-- 数据库连接 -->
    <Connection class="com.fr.data.impl.NameDatabaseConnection">
        <DatabaseName><![CDATA[sales_db]]></DatabaseName>
    </Connection>
    
    <!-- SQL 查询 -->
    <Query><![CDATA[
        SELECT region, product, SUM(amount) as amount 
        FROM sales 
        WHERE date >= '${startDate}' 
        AND region = '${region}'
        GROUP BY region, product
    ]]></Query>
</TableData>
```

#### 参数引用语法

```sql
-- 直接引用参数
WHERE date = '${dateParam}'

-- 条件判断
${if(len(region)=0, "", "AND region = '" + region + "'")}

-- 空值处理
${if(len(orgId)=0, "AND 1=2", "AND org_id IN (" + orgId + ")")}
```

### 2.3 筛选区域模块 (ReportParameterAttr)

#### 控件类型

| 控件 | 类名 | 适用场景 |
|------|------|----------|
| 文本输入 | `TextEditor` | 协议编号、名称搜索 |
| 日期选择 | `DateEditor` | 开始日期、结束日期 |
| 下拉单选 | `ComboBox` | 币种、状态、类型 |
| 下拉多选 | `ComboCheckBox` | 多个区域、多个产品 |
| 树形选择 | `TreeComboBoxEditor` | 组织机构、部门 |

#### XML 结构示例

```xml
<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
    <InnerWidget class="com.fr.form.ui.DateEditor">
        <WidgetName name="startDate"/>
        <LabelName name="开始日期"/>
        <WidgetAttr>
            <PrivilegeControl/>
        </WidgetAttr>
        <DateAttr/>
        <widgetValue>
            <O><![CDATA[]]></O>
        </widgetValue>
    </InnerWidget>
    <BoundsAttr x="100" y="10" width="135" height="28"/>
</Widget>

<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
    <InnerWidget class="com.fr.form.ui.ComboBox">
        <WidgetName name="currencyCode"/>
        <LabelName name="币种"/>
        <Dictionary class="com.fr.data.impl.TableDataDictionary">
            <FormulaDictAttr kiName="dict_key" viName="dict_value"/>
            <TableDataDictAttr>
                <TableData class="com.fr.data.impl.NameTableData">
                    <Name><![CDATA[currency]]></Name>
                </TableData>
            </TableDataDictAttr>
        </Dictionary>
    </InnerWidget>
    <BoundsAttr x="250" y="10" width="135" height="28"/>
</Widget>
```

#### 数据字典配置

```xml
<!-- 静态选项 -->
<Dictionary class="com.fr.data.impl.CustomDictionary">
    <CustomDictAttr>
        <Dict key="CNY" value="人民币"/>
        <Dict key="USD" value="美元"/>
        <Dict key="EUR" value="欧元"/>
    </CustomDictAttr>
</Dictionary>

<!-- 动态选项（从数据集获取） -->
<Dictionary class="com.fr.data.impl.TableDataDictionary">
    <FormulaDictAttr kiName="dict_key" viName="dict_value"/>
    <TableDataDictAttr>
        <TableData class="com.fr.data.impl.NameTableData">
            <Name><![CDATA[currency]]></Name>
        </TableData>
    </TableDataDictAttr>
</Dictionary>
```

### 2.4 数据展示区模块 (Report)

#### 单元格结构

```xml
<CellElementList>
    <!-- 表头：静态文本 -->
    <C c="0" r="0" s="0">
        <O><![CDATA[区域]]></O>
        <PrivilegeControl/>
        <Expand/>
    </C>
    
    <!-- 数据绑定：从数据集取值 -->
    <C c="0" r="1" s="1">
        <O t="DSColumn">
            <Attributes dsName="sales_data" columnName="region"/>
            <Complex/>
            <RG class="com.fr.report.cell.cellattr.core.group.FunctionGrouper"/>
        </O>
        <Expand dir="0"/>  <!-- 纵向扩展 -->
    </C>
    
    <!-- 公式：汇总计算 -->
    <C c="2" r="5" s="2">
        <O t="XMLable" class="com.fr.base.Formula">
            <Attributes><![CDATA[=SUM(C2,C3,C4,C5)]]></Attributes>
        </O>
        <Expand/>
    </C>
</CellElementList>
```

#### 单元格属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `c` | 列号（0开始） | `c="0"` |
| `r` | 行号（0开始） | `r="1"` |
| `rs` | 行合并数 | `rs="2"` |
| `cs` | 列合并数 | `cs="3"` |
| `s` | 样式索引 | `s="0"` |

#### 值类型

| 类型 | 说明 | XML 表示 |
|------|------|----------|
| 静态文本 | 固定内容 | `<O><![CDATA[文本]]></O>` |
| 数据绑定 | 从数据集取值 | `<O t="DSColumn">` |
| 公式 | 计算表达式 | `<O t="XMLable" class="com.fr.base.Formula">` |

#### 扩展方向

| 值 | 说明 |
|----|------|
| `dir="0"` | 纵向扩展（向下） |
| `dir="1"` | 横向扩展（向右） |
| 无 | 不扩展 |

---

## 三、Agent 整体架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户输入                                  │
│              "创建销售报表，按区域分组，显示金额、数量"            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     需求解析器 (RequirementParser)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  标题提取    │  │  数据源识别  │  │  筛选条件识别 │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  分组识别    │  │  聚合识别    │  │  控件类型推断 │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     结构化配置 (ReportSpec)                      │
│  {                                                              │
│    "title": "销售报表",                                          │
│    "data_source": { "table": "sales", "fields": [...] },        │
│    "filter_controls": [{ "name": "region", "type": "ComboBox" }],│
│    "display": { "columns": [...], "group_rows": [...] }         │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CPT 生成器 (CPTGenerator)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 生成数据源   │  │ 生成筛选面板 │  │ 生成单元格   │          │
│  │ TableDataMap │  │ ParameterUI  │  │ CellElements │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 生成 SQL     │  │ 生成控件布局 │  │ 生成样式     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      输出: .cpt 文件                             │
│  <?xml version="1.0" encoding="UTF-8"?>                         │
│  <WorkBook xmlVersion="20211223" releaseVersion="11.5.0">       │
│    ...                                                          │
│  </WorkBook>                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **需求解析器** | 理解自然语言需求 | 文本描述 | ReportSpec |
| **CPT 解析器** | 解析现有报表 | .cpt 文件 | CPTStructure |
| **CPT 生成器** | 生成报表文件 | 配置字典 | .cpt XML |

---

## 四、工作流程详解

### 4.1 从自然语言生成报表

#### 步骤 1：需求解析

```python
# 输入
requirement = "创建销售报表，按区域分组，显示金额、数量，筛选条件：日期范围、区域"

# 解析过程
parser = RequirementParser()
spec = parser.parse(requirement)

# 输出
spec.title = "销售报表"
spec.data_source.table = "sales"
spec.data_source.group_by = ["region"]
spec.data_source.fields = ["金额", "数量"]
spec.filter_controls = [
    FilterControlSpec(name="startDate", type="DateEditor", label="开始日期"),
    FilterControlSpec(name="endDate", type="DateEditor", label="结束日期"),
    FilterControlSpec(name="region", type="ComboBox", label="区域")
]
```

#### 步骤 2：SQL 生成

```python
def _generate_sql(spec: DataSourceSpec) -> str:
    """根据规格生成 SQL"""
    
    # SELECT 字段
    fields = []
    for field in spec.fields:
        if field in spec.aggregations:
            agg = spec.aggregations[field]  # sum, avg, count...
            fields.append(f"{agg}({field}) AS {field}")
        else:
            fields.append(field)
    
    # 基础 SQL
    sql = f"SELECT {', '.join(fields)} FROM {spec.table}"
    
    # WHERE 参数化条件
    conditions = []
    for ctrl in spec.filter_controls:
        if ctrl.control_type == "DateEditor":
            conditions.append(f"${{if(len({ctrl.name})=0,'','AND {ctrl.name} = ${{{ctrl.name}}}')")
        elif ctrl.control_type == "ComboBox":
            conditions.append(f"${{if(len({ctrl.name})=0,'','AND {ctrl.name} = ${{{ctrl.name}}}')")
    
    if conditions:
        sql += " WHERE 1=1 " + " ".join(conditions)
    
    # GROUP BY
    if spec.group_by:
        sql += f" GROUP BY {', '.join(spec.group_by)}"
    
    return sql
```

#### 步骤 3：筛选面板生成

```python
def generate_filter_panel(controls: List[FilterControlSpec]) -> ET.Element:
    """生成筛选面板 XML"""
    
    layout = ET.Element('Layout')
    layout.set('class', 'com.fr.form.ui.container.WParameterLayout')
    
    for i, ctrl in enumerate(controls):
        widget = create_widget(ctrl, i)
        layout.append(widget)
    
    # 添加查询按钮
    search_btn = create_search_button()
    layout.append(search_btn)
    
    return layout

def create_widget(ctrl: FilterControlSpec, index: int) -> ET.Element:
    """创建控件"""
    
    # 根据类型选择控件类
    widget_class = {
        "TextEditor": "com.fr.form.ui.TextEditor",
        "DateEditor": "com.fr.form.ui.DateEditor",
        "ComboBox": "com.fr.form.ui.ComboBox",
        "TreeComboBoxEditor": "com.fr.form.ui.TreeComboBoxEditor",
    }[ctrl.control_type]
    
    # 计算位置
    x = 100 + (index % 4) * 180
    y = 10 + (index // 4) * 35
    
    # 构建 XML
    widget = ET.Element('Widget')
    inner = ET.SubElement(widget, 'InnerWidget')
    inner.set('class', widget_class)
    
    name = ET.SubElement(inner, 'WidgetName')
    name.set('name', ctrl.name)
    
    # ... 其他属性
    
    return widget
```

#### 步骤 4：单元格生成

```python
def generate_cells(spec: DisplaySpec, ds_name: str) -> List[ET.Element]:
    """生成单元格列表"""
    
    cells = []
    
    # 第 0 行：表头
    for col_idx, col_name in enumerate(spec.columns):
        cell = create_header_cell(col_idx, col_name)
        cells.append(cell)
    
    # 第 1 行：数据绑定
    for col_idx, col_name in enumerate(spec.columns):
        cell = create_data_cell(col_idx, 1, ds_name, col_name)
        # 第一列设置扩展
        if col_idx == 0:
            cell.set('dir', '0')
        cells.append(cell)
    
    # 汇总行
    if spec.summary_row:
        for col_idx, col_name in enumerate(spec.columns):
            if col_idx > 0:  # 跳过分组列
                cell = create_formula_cell(col_idx, 2, f"=SUM({chr(65+col_idx)}2)")
                cells.append(cell)
    
    return cells
```

### 4.2 从现有报表学习

#### 步骤 1：解析报表结构

```python
parser = CPTParser()
structure = parser.parse("FinanceCreditContractAnalysis.cpt")

# 提取信息
structure.table_data_list  # 数据源列表
structure.widget_controls  # 筛选控件列表
structure.cell_elements    # 单元格列表
```

#### 步骤 2：生成模板

从解析的结构中提取：
- 数据源 SQL 模板
- 控件布局模板
- 单元格样式模板

#### 步骤 3：应用到新报表

基于模板生成新报表。

---

## 五、核心数据结构

### 5.1 ReportSpec（报表规格）

```python
@dataclass
class ReportSpec:
    """报表规格"""
    title: str                              # 报表标题
    description: str                        # 原始描述
    data_source: DataSourceSpec             # 数据源规格
    filter_controls: List[FilterControlSpec] # 筛选控件
    display: DisplaySpec                    # 展示规格

@dataclass
class DataSourceSpec:
    """数据源规格"""
    name: str                               # 数据源名称
    database: str                           # 数据库名
    table: str                              # 表名
    fields: List[str]                       # 字段列表
    filters: List[str]                      # 过滤条件
    group_by: List[str]                     # 分组字段
    aggregations: Dict[str, str]            # 聚合函数 {字段: 函数}

@dataclass
class FilterControlSpec:
    """筛选控件规格"""
    name: str                               # 参数名
    label: str                              # 显示标签
    control_type: str                       # 控件类型
    data_type: str                          # 数据类型
    options: Dict[str, str]                 # 下拉选项
    source_table: str                       # 数据来源表
    source_field: str                       # 数据来源字段

@dataclass
class DisplaySpec:
    """展示规格"""
    columns: List[str]                      # 列名
    group_rows: List[str]                   # 分组行
    summary_row: bool                       # 是否有汇总行
    chart_type: str                         # 图表类型
```

### 5.2 CPTStructure（CPT 结构）

```python
@dataclass
class CPTStructure:
    """CPT 文件结构"""
    title: str
    table_data_list: List[TableData]        # 数据源列表
    widget_controls: List[WidgetControl]    # 控件列表
    cell_elements: List[CellElement]        # 单元格列表
    styles: List[Dict]                      # 样式列表
    javascript_listeners: List[Dict]        # JS 监听器
```

---

## 六、扩展计划

### 6.1 短期目标

- [ ] 完善需求解析器，支持更复杂的自然语言
- [ ] 支持更多控件类型（树形、级联等）
- [ ] 自动布局算法优化
- [ ] 样式模板库

### 6.2 中期目标

- [ ] GUI 可视化配置界面
- [ ] 从数据库 Schema 自动生成报表
- [ ] 报表版本管理
- [ ] 批量报表生成

### 6.3 长期目标

- [ ] AI 辅助设计（智能推荐布局）
- [ ] 报表测试自动化
- [ ] 多数据源支持
- [ ] 移动端适配

---

## 七、使用示例

### 示例 1：简单列表报表

**输入**：
```
创建客户列表报表，显示客户名称、联系人、电话
```

**生成**：
- 数据源：SELECT * FROM customers
- 筛选：无
- 展示：3列数据表格

### 示例 2：分组汇总报表

**输入**：
```
创建销售统计报表，数据源：sales，按区域分组，显示销售额、数量，筛选条件：日期范围、区域
```

**生成**：
- 数据源：
  ```sql
  SELECT region, SUM(amount) as amount, COUNT(*) as quantity
  FROM sales
  WHERE date >= '${startDate}' AND date <= '${endDate}'
  GROUP BY region
  ```
- 筛选：开始日期、结束日期、区域下拉
- 展示：分组表格 + 汇总行

### 示例 3：多 Sheet 报表

**输入**：
```
创建授信一览报表，包含4个Sheet：
1. 按授信类型统计
2. 按被授信人统计
3. 按授信机构统计
4. 按授信产品统计
```

**生成**：
- 数据源：4个 ClassTableData
- 筛选：统一的参数面板
- 展示：4个 Sheet，每个一个统计表

---

## 八、技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| XML 处理 | xml.etree.ElementTree |
| GUI | tkinter / PyQt |
| AI 集成 | OpenAI API / Claude API |

---

## 九、参考资源

- [帆软官方文档](https://help.fanruan.com/)
- [FineReport 开发指南](https://help.fanruan.com/finereport/)
- 示例报表：`/home/admin/FinanceCreditContractAnalysis.cpt`