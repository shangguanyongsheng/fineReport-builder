# CPT 模板核心标签标注

> 对模板文件的核心 XML 标签进行标注，用于生成 CPT 检查和验证。

---

## 📁 目录结构

```
fineReport-builder/
├── examples/                         # 模板文件（只读参考）
│   └── FinanceCreditContractAnalysisDetail.cpt  # 明细报表模板 ⭐
│
├── templates/
│   ├── CPT_TEMPLATE_ANNOTATION.md    # 本文档
│   └── target/                       # 目标 CPT 目录
│
└── outputs/                          # 输出目录（生成的报表文件）
```

---

## 📋 模板文件说明

| 模板文件 | 类型 | 大小 | 用途 |
|----------|------|------|------|
| FinanceCreditContractAnalysisDetail.cpt | 明细报表 | 168KB | 授信合同明细报表模板 |

---

## 🏗️ CPT 文件结构概览

以 `FinanceCreditContractAnalysisDetail.cpt` 明细报表为例：

```
<?xml version="1.0" encoding="UTF-8"?>
<WorkBook xmlVersion="20211223" releaseVersion="11.5.0">
│
├── 📦 TableDataMap              【数据源映射】行 3-1296
│   ├── DBTableData              数据库数据源
│   ├── ClassTableData           Java 类数据源 ⭐ 核心标签（行 109, 273, 394, 510, 665, 791）
│   └── RecursionTableData       递归树数据源
│
├── 📄 ReportWebAttr             【Web 属性】
│   └── Title                    报表标题
│
├── 📊 Report                    【报表主体】行 1297-3454
│   ├── ReportPageAttr           页面属性
│   ├── RowHeight                行高 ⭐ 见下方规范
│   ├── ColumnWidth              列宽 ⭐ 见下方规范
│   ├── CellElementList          单元格列表 ⭐ 核心标签（行 1297-3454）
│   ├── ReportAttrSet            报表属性集
│   └── PrivilegeControl         权限控制
│
├── 🎛️ ReportParameterAttr       【参数面板】行 3480-5469
│   ├── Attributes               面板属性
│   ├── PWTitle                  面板标题
│   ├── ParameterUI              参数 UI ⭐ 核心标签
│   │   └── Layout               布局容器
│   │       └── Widget           控件列表
│
└── 🎨 StyleList                 【样式列表】行 5470-5612
    └── Style                    样式定义 ⭐ 核心标签
</WorkBook>
```

---

## 📏 行高列宽规范

**单位换算：1 pt = 12700 EMU**

### 模板实际值

| 配置 | pt | EMU | 说明 |
|------|-----|-----|------|
| 表头行高 | 107.7 pt | 1368000 | 第0行（表头行） |
| 数据行高 | 57 pt | 723900 | 第1行及以后（数据行） |
| 数据列宽 | 362.8 pt | 4608000 | 普通数据列 |
| 默认列宽 | 216 pt | 2743200 | 默认值 |

### XML 结构

```xml
<!-- 行高：defaultValue 为默认行高，CDATA 内为每行具体值 -->
<RowHeight defaultValue="723900">
<![CDATA[1368000,723900]]></RowHeight>
<!-- 解析：第0行 1368000 (表头)，第1行 723900 (数据) -->

<!-- 列宽：defaultValue 为默认列宽，CDATA 内为每列具体值 -->
<ColumnWidth defaultValue="2743200">
<![CDATA[4608000,4608000,4608000]]></ColumnWidth>
<!-- 解析：每列都是 4608000 -->
```

### 计算公式

```python
# 行高列表：表头行用 header_height，其他用 default_height
def calc_row_heights(max_row, header_height=1368000, default_height=723900):
    return [header_height if r == 0 else default_height for r in range(max_row + 1)]

# 列宽列表：统一使用 data_width
def calc_col_widths(max_col, data_width=4608000):
    return [data_width] * (max_col + 1)
```

---

## 📦 一、TableDataMap 数据源映射

### 1.1 ClassTableData 结构 ⭐ 核心标签

**位置**：行 109-259

```xml
<!-- ========== ClassTableData 结构标注 ========== -->
<TableData name="CreditContractDetailData" 
           class="com.fr.data.impl.ClassTableData">
    
    <!-- 【必需】脱敏设置 -->
    <Desensitizations desensitizeOpen="false"/>
    
    <!-- 【核心】参数列表 - 与筛选组件绑定 -->
    <Parameters>
        <Parameter>
            <Attributes name="orgId"/>           <!-- 参数名 -->
            <O><![CDATA[]]></O>                   <!-- 默认值，空=从筛选组件获取 -->
        </Parameter>
        <Parameter>
            <Attributes name="startDate"/>
            <O><![CDATA[]]></O>
        </Parameter>
        <Parameter>
            <Attributes name="indexInfo"/>
            <O><![CDATA[{"fieldCode": "repay.id"}]]></O>  <!-- 有值=写死默认值 -->
        </Parameter>
    </Parameters>
    
    <!-- 【必需】Java 类全路径 -->
    <ClassTableDataAttr className="com.yocyl.fr.engine.tableData.finance.CreditContractDetailData"/>
</TableData>
```

### 1.2 DBTableData 结构

```xml
<!-- ========== DBTableData 结构标注 ========== -->
<TableData name="orgStructure" class="com.fr.data.impl.DBTableData">
    
    <Desensitizations desensitizeOpen="false"/>
    
    <!-- 参数列表 -->
    <Parameters>
        <Parameter>
            <Attributes name="fine_username9"/>
            <O><![CDATA[]]></O>
        </Parameter>
    </Parameters>
    
    <Attributes maxMemRowCount="-1"/>
    
    <!-- 数据库连接 -->
    <Connection class="com.fr.data.impl.NameDatabaseConnection">
        <DatabaseName><![CDATA[cfs-report]]></DatabaseName>
    </Connection>
    
    <!-- SQL 查询 - 使用 ${paramName} 引用参数 -->
    <Query><![CDATA[
        SELECT * FROM table WHERE tenant_id = '${fine_username9}'
    ]]></Query>
    
    <PageQuery><![CDATA[]]></PageQuery>
</TableData>
```

### 1.3 关键字段说明

| 标签 | 属性 | 说明 | 必需 |
|------|------|------|------|
| `TableData` | `name` | 数据源名称，全局唯一 | ✅ |
| `TableData` | `class` | 数据源类型 | ✅ |
| `Parameters` | - | 参数容器，ClassTableData 必须有 | ✅ |
| `Parameter/Attributes` | `name` | 参数名，与筛选组件 code 对应 | ✅ |
| `Parameter/O` | - | 默认值，空=动态获取 | ✅ |
| `ClassTableDataAttr` | `className` | Java 类全路径 | ✅ |

---

## 📊 二、CellElementList 单元格列表

**位置**：行 1297-3454

### 2.1 表头单元格

```xml
<!-- ========== 表头单元格标注 ========== -->
<!-- rs="6" 表示合并 6 行 -->
<C c="0" r="0" rs="6" s="0">
    <O><![CDATA[授信类型]]></O>    <!-- 静态文本 -->
    <PrivilegeControl/>
    <Expand>
        <cellSortAttr/>
    </Expand>
</C>

<!-- 普通表头单元格 -->
<C c="1" r="0" s="1">
    <O><![CDATA[币种]]></O>
    <PrivilegeControl/>
    <Expand>
        <cellSortAttr/>
    </Expand>
</C>
```

### 2.2 数据单元格（DSColumn）

```xml
<!-- ========== 数据单元格标注 ========== -->
<C c="1" r="1" s="2">
    <!-- 静态文本 -->
    <O><![CDATA[综合授信]]></O>
    <PrivilegeControl/>
    <CellGUIAttr adjustmode="2" showAsDefault="true"/>
    <CellPageAttr/>
    
    <!-- 扩展方向：dir="0" 纵向扩展 -->
    <Expand dir="0">
        <cellSortAttr/>
    </Expand>
</C>
```

### 2.3 单元格属性说明

| 属性 | 说明 | 示例 |
|------|------|------|
| `c` | 列索引（0 开始） | `c="0"` |
| `r` | 行索引（0 开始） | `r="0"` |
| `rs` | 行合并数 | `rs="6"` |
| `cs` | 列合并数 | `cs="2"` |
| `s` | 样式索引 | `s="0"` |

### 2.4 单元格值类型

| 类型 | XML 表示 | 说明 |
|------|----------|------|
| 静态文本 | `<O><![CDATA[文本]]></O>` | 固定内容 |
| 数据绑定 | `<O t="DSColumn">` | 从数据源取值 |
| 公式 | `<O t="XMLable" class="Formula">` | 计算表达式 |

---

## 🎛️ 三、ReportParameterAttr 参数面板

**位置**：行 3480-5469

### 3.1 参数面板结构

```xml
<!-- ========== 参数面板结构标注 ========== -->
<ReportParameterAttr>
    <!-- 面板属性 -->
    <Attributes showWindow="true" delayPlaying="false" 
                windowPosition="1" align="0" 
                useParamsTemplate="true" currentIndex="8"/>
    
    <!-- 面板标题 -->
    <PWTitle><![CDATA[参数]]></PWTitle>
    
    <!-- 参数 UI 容器 -->
    <ParameterUI class="com.fr.form.main.parameter.FormParameterUI">
        <Parameters/>
        
        <!-- 布局容器 -->
        <Layout class="com.fr.form.ui.container.WParameterLayout">
            <WidgetName name="para"/>
            <WidgetAttr>...</WidgetAttr>
            
            <!-- ========== 控件列表 ========== -->
            <!-- 控件 1: ComboCheckBox -->
            <Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
                <InnerWidget class="com.fr.form.ui.ComboCheckBox">
                    <WidgetName name="financeTypeCode2"/>    <!-- 参数名 -->
                    <WidgetID widgetID="..."/>
                    
                    <!-- 下拉选项（静态） -->
                    <Dictionary class="com.fr.data.impl.CustomDictionary">
                        <CustomDictAttr>
                            <Dict key="ZHSX" value="综合授信"/>
                            <Dict key="NBSX" value="内部授信"/>
                        </CustomDictAttr>
                    </Dictionary>
                    
                    <!-- 默认值 -->
                    <widgetValue>
                        <O><![CDATA[]]></O>
                    </widgetValue>
                </InnerWidget>
                
                <!-- 位置和尺寸 -->
                <BoundsAttr x="1029" y="83" width="135" height="28"/>
            </Widget>
            
            <!-- 控件 2: Label -->
            <Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
                <InnerWidget class="com.fr.form.ui.Label">
                    <WidgetName name="授信类型2"/>
                    <LabelName name="批文/授信"/>         <!-- 显示文本 -->
                    
                    <widgetValue>
                        <O><![CDATA[授信类型]]></O>
                    </widgetValue>
                </InnerWidget>
                <BoundsAttr x="936" y="83" width="89" height="28"/>
            </Widget>
        </Layout>
    </ParameterUI>
</ReportParameterAttr>
```

### 3.2 控件类型对照

| 控件类型 | class 属性 | 说明 |
|----------|-----------|------|
| 文本框 | `com.fr.form.ui.TextEditor` | 单行文本输入 |
| 日期 | `com.fr.form.ui.DateEditor` | 日期选择器 |
| 下拉框 | `com.fr.form.ui.ComboBox` | 单选下拉 |
| 多选下拉 | `com.fr.form.ui.ComboCheckBox` | 多选下拉 |
| 树形下拉 | `com.fr.form.ui.TreeComboBoxEditor` | 树形选择 |
| 数字 | `com.fr.form.ui.NumberEditor` | 数字输入 |
| 标签 | `com.fr.form.ui.Label` | 纯文本显示 |

### 3.3 控件位置规范

```
布局规则：每行 5 对控件（Label + 输入控件）

Label 尺寸：89px × 28px
输入控件尺寸：135px × 28px
Label 与输入控件间距：4px
控件对之间间距：10px
行间距：36px

位置计算公式：
  行号 row = index // 5
  列号 col = index % 5
  
  Label_X = 10 + col × (89 + 4 + 135 + 10)
  Input_X = Label_X + 89 + 4
  Y = 10 + row × 36
```

---

## 🎨 四、StyleList 样式列表

**位置**：行 5470-5612

### 4.1 样式结构

```xml
<!-- ========== 样式列表标注 ========== -->
<StyleList>
    <!-- Style 0: 表头左列样式 -->
    <Style style_name="表头左列" horizontal_alignment="2">
        <FRFont name="SimSun" style="0" size="80"/>
        <Background name="ColorBackground">
            <color>
                <FineColor color="-1447425"/>    <!-- 淡蓝色 -->
            </color>
        </Background>
        <Border>
            <Top style="1">
                <FineColor color="-2432266"/>     <!-- 边框颜色 -->
            </Top>
            <Bottom style="1">...</Bottom>
            <Left style="1">...</Left>
            <Right style="1">...</Right>
        </Border>
    </Style>
    
    <!-- Style 1: 表头样式 -->
    <Style style_name="表头" horizontal_alignment="2">
        ...
    </Style>
    
    <!-- Style 3: 金额样式（右对齐 + 数字格式） -->
    <Style style_name="金额" horizontal_alignment="4">
        <Format class="com.fr.base.CoreDecimalFormat" 
                roundingMode="6">
            #,##0.00
        </Format>
        <FRFont name="SimSun" style="0" size="80">
            <foreground>
                <FineColor color="-8163329"/>    <!-- 蓝色字体 -->
            </foreground>
        </FRFont>
        ...
    </Style>
</StyleList>
```

### 4.2 样式属性说明

| 属性 | 说明 | 值 |
|------|------|-----|
| `style_name` | 样式名称 | 中文描述 |
| `horizontal_alignment` | 水平对齐 | 0=中, 2=左, 4=右 |
| `FRFont@name` | 字体名称 | SimSun, 宋体, simhei |
| `FRFont@size` | 字号 | 80=10pt |
| `FRFont@style` | 字体样式 | 0=常规, 1=粗体 |
| `Background@name` | 背景类型 | ColorBackground, NullBackground |
| `FineColor@color` | 颜色值 | 十进制颜色值 |

### 4.3 颜色对照表

| 颜色 | RGB | 十进制值 | 用途 |
|------|-----|----------|------|
| 白色 | (255,255,255) | -1 | 纯白背景 |
| 蓝色背景 | (233,233,255) | **-1447425** | 表头背景 |
| 边框灰 | (218,226,246) | -2432266 | 边框颜色 |
| 蓝色字体 | (0,102,204) | -8163329 | 金额字体颜色 |

**颜色计算公式**（Java 有符号32位整数）：
```
RGB(233, 233, 255) → 0xFFE9E9FF → -1447425
RGB(218, 226, 246) → 0xFFDAE2F6 → -2432266
```

---

## ✅ 五、生成 CPT 检查清单

### 5.1 必需检查项

| 检查项 | 标签 | 检查内容 |
|--------|------|----------|
| ✅ ClassTableData 参数 | `<Parameters>` | 必须存在，不能为空 |
| ✅ 参数 CDATA 格式 | `<O><![CDATA[]]></O>` | 必须使用 CDATA 格式 |
| ✅ 参数名绑定 | `@name` | 与筛选组件 code 一致 |
| ✅ 控件名称 | `<WidgetName>` | 与数据源参数名一致 |
| ✅ 样式索引 | `@s` | 在 StyleList 范围内 |

### 5.2 检查脚本示例

```python
def validate_cpt(cpt_path: str) -> dict:
    """验证生成的 CPT 文件"""
    import xml.etree.ElementTree as ET
    
    issues = []
    
    tree = ET.parse(cpt_path)
    root = tree.getroot()
    
    # 1. 检查 ClassTableData 参数
    for table_data in root.findall('.//TableData[@class="com.fr.data.impl.ClassTableData"]'):
        name = table_data.get('name')
        params = table_data.find('Parameters')
        
        if params is None:
            issues.append(f"❌ [{name}] 缺少 <Parameters> 节点")
        elif len(params.findall('Parameter')) == 0:
            issues.append(f"⚠️ [{name}] Parameters 为空")
    
    # 2. 检查样式索引范围
    style_count = len(root.findall('.//StyleList/Style'))
    for cell in root.findall('.//C[@s]'):
        s = int(cell.get('s'))
        if s >= style_count:
            issues.append(f"❌ 单元格样式索引越界: s={s}, 最大={style_count-1}")
    
    # 3. 检查筛选组件与数据源参数绑定
    widget_names = set()
    for widget in root.findall('.//WidgetName'):
        name = widget.get('name')
        if name and not name.startswith('label_'):
            widget_names.add(name)
    
    param_names = set()
    for param in root.findall('.//Parameter/Attributes[@name]'):
        param_names.add(param.get('name'))
    
    unbound = param_names - widget_names
    if unbound:
        issues.append(f"⚠️ 参数无对应筛选组件: {unbound}")
    
    return {
        'valid': len([i for i in issues if i.startswith('❌')]) == 0,
        'issues': issues
    }
```

---

## 📝 六、目标 CPT 目录规范

### 6.1 目录结构

```
templates/target/
├── management/                  # 管理分析报表目标
│   ├── basic.json              # 基础配置
│   ├── filter_template.json    # 筛选组件模板
│   └── style_template.json     # 样式模板
│
├── detail/                      # 明细报表目标
│   ├── basic.json
│   ├── filter_template.json
│   └── style_template.json
│
└── README.md                    # 目标目录说明
```

### 6.2 目标配置示例

```json
{
  "template_type": "management",
  "target_name": "管理分析报表",
  
  "data_source": {
    "type": "ClassTableData",
    "name": "CreditContractDetailData",
    "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
    "required_params": ["orgId", "startDate", "endDate"]
  },
  
  "filter_layout": {
    "pairs_per_row": 5,
    "label_width": 89,
    "input_width": 135,
    "row_gap": 36,
    "start_x": 10,
    "start_y": 10
  },
  
  "data_area": {
    "header_row": 0,
    "data_row": 1,
    "max_columns": 10
  }
}
```

---

_📅 标注日期：2026-04-09_
_📋 模板文件：FinanceCreditContractAnalysisDetail.cpt（明细报表）_