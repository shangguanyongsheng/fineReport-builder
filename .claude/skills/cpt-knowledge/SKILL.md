---
name: cpt-knowledge
description: 加载帆软 CPT 知识库上下文，理解 CPT 文件结构、XML 标签规范、控件类型、样式系统等核心概念。在开始任何报表开发任务前首先加载此技能。
type: reference

---

# 帆软 CPT 知识库

## 一、CPT 文件整体结构

`.cpt` 是帆软报表的文件格式，本质是 XML 文件。根节点为 `<WorkBook>`。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WorkBook xmlVersion="20211223" releaseVersion="11.5.0">
    <TableDataMap>...</TableDataMap>        <!-- 数据源映射 -->
    <ReportWebAttr>...</ReportWebAttr>      <!-- Web 属性 -->
    <Report>...</Report>                     <!-- 报表主体（单元格、行高列宽） -->
    <ReportParameterAttr>...</ReportParameterAttr>  <!-- 参数面板（筛选组件） -->
    <StyleList>...</StyleList>              <!-- 样式列表 -->
    <DesensitizationList/>                  <!-- 脱敏列表 -->
    <DesignerVersion DesignerVersion="LAA"/>
    <PreviewType PreviewType="2"/>
    <ForkIdAttrMark class="com.fr.base.iofile.attr.ForkIdAttrMark">
        <ForkIdAttrMark forkId="UUID"/>
    </ForkIdAttrMark>
</WorkBook>
```

## 二、TableDataMap — 数据源映射

### ClassTableData（Java 类数据源）⭐ 最常用

```xml
<TableData name="数据源名称" class="com.fr.data.impl.ClassTableData">
    <Desensitizations desensitizeOpen="false"/>
    <Parameters>
        <Parameter>
            <Attributes name="参数名"/>
            <O><![CDATA[默认值]]></O>
        </Parameter>
    </Parameters>
    <ClassTableDataAttr className="com.yocyl.fr.engine.tableData.finance.XXXData"/>
</TableData>
```

**关键规则**：
- `Parameters` 节点**必须存在**，即使为空
- `<O>` 标签**必须使用 CDATA 格式**
- 默认值为空字符串 `""` → 从筛选组件动态获取
- 默认值有内容 → 固定默认值

### DBTableData（数据库数据源）

```xml
<TableData name="数据源名称" class="com.fr.data.impl.DBTableData">
    <Desensitizations desensitizeOpen="false"/>
    <Parameters>...</Parameters>
    <Connection class="com.fr.data.impl.NameDatabaseConnection">
        <DatabaseName><![CDATA[数据库连接名]]></DatabaseName>
    </Connection>
    <Query><![CDATA[SELECT ... WHERE x = '${参数名}']]></Query>
    <PageQuery><![CDATA[]]></PageQuery>
</TableData>
```

## 三、ReportParameterAttr — 参数面板（筛选组件）

### 布局规范

```
每行 5 对控件（Label + 输入控件）
Label 尺寸：89px × 28px
输入控件尺寸：135px × 28px
Label 与输入框间距：4px
同一行组件间距：4px（统一）
行间距：8px
起始坐标：x=10, y=10

位置计算：
  row = index // 5
  col = index % 5
  pair_width = 89 + 4 + 135 = 228
  Label_X = 10 + col × (228 + 4)
  Input_X = Label_X + 89 + 4
  Y = 10 + row × (28 + 8)
```

### Label 控件 XML

```xml
<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
    <InnerWidget class="com.fr.form.ui.Label">
        <WidgetName name="label_0"/>
        <widgetValue>
            <O>显示文本</O>
        </widgetValue>
    </InnerWidget>
    <BoundsAttr x="10" y="10" width="89" height="28"/>
</Widget>
```

### 输入控件 XML

```xml
<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
    <InnerWidget class="com.fr.form.ui.TextEditor">  <!-- 或 DateEditor/ComboBox 等 -->
        <WidgetName name="参数code"/>
        <widgetValue>
            <O><![CDATA[]]></O>  <!-- 默认值 -->
        </widgetValue>
    </InnerWidget>
    <BoundsAttr x="103" y="10" width="135" height="28"/>
</Widget>
```

### 支持的控件类型

| 控件类型 | InnerWidget class | 说明 |
|----------|-------------------|------|
| TextEditor | `com.fr.form.ui.TextEditor` | 单行文本输入 |
| DateEditor | `com.fr.form.ui.DateEditor` | 日期选择器 |
| ComboBox | `com.fr.form.ui.ComboBox` | 单选下拉 |
| ComboCheckBox | `com.fr.form.ui.ComboCheckBox` | 多选下拉（用于动态列） |
| TreeComboBoxEditor | `com.fr.form.ui.TreeComboBoxEditor` | 树形下拉 |
| NumberEditor | `com.fr.form.ui.NumberEditor` | 数字输入 |
| Label | `com.fr.form.ui.Label` | 纯文本标签 |

## 四、Report — 报表主体

### 行高列宽

```xml
<!-- 单位：EMU，1 pt = 12700 EMU -->
<RowHeight defaultValue="723900">
<![CDATA[1368000,723900,723900]]>
</RowHeight>
<!-- 第0行=表头1368000，第1行及以后=数据723900 -->

<ColumnWidth defaultValue="2743200">
<![CDATA[4608000,4608000,4608000]]>
</ColumnWidth>
<!-- 每列宽度 4608000 (362.8pt) -->
```

### 单元格列表 CellElementList

#### 表头单元格（静态文本）

```xml
<C c="0" r="0" s="1">
    <O><![CDATA[合同编号]]></O>
    <PrivilegeControl/>
    <Expand>
        <cellSortAttr/>
    </Expand>
</C>
```

#### 数据单元格（绑定数据源字段）

```xml
<C c="0" r="1" s="2">
    <O t="DSColumn">
        <Attributes dsName="数据源名称" columnName="字段名"/>
    </O>
    <PrivilegeControl/>
    <Expand dir="0">
        <cellSortAttr/>
    </Expand>
</C>
```

#### 序号列（seq() 公式）

```xml
<C c="0" r="1" s="2">
    <O t="XMLable" class="com.fr.base.Formula">seq()</O>
    <PrivilegeControl/>
    <Expand dir="0"/>
</C>
```

### 单元格属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `c` | 列索引（0 开始） | `c="0"` |
| `r` | 行索引（0 开始） | `r="0"` |
| `rs` | 行合并数 | `rs="6"` |
| `cs` | 列合并数 | `cs="2"` |
| `s` | 样式索引 | `s="0"` |

### 单元格值类型

| 类型 | XML 表示 | 说明 |
|------|----------|------|
| 静态文本 | `<O><![CDATA[文本]]></O>` | 固定内容，表头用 |
| 数据绑定 | `<O t="DSColumn"><Attributes dsName="xxx" columnName="xxx"/></O>` | 从数据源取值 |
| 公式 | `<O t="XMLable" class="com.fr.base.Formula">公式</O>` | 计算表达式 |

## 五、StyleList — 样式列表

### 默认样式集（5 种）

| 索引 | 名称 | 水平对齐 | 背景 | 边框 | 字体 | 用途 |
|------|------|----------|------|------|------|------|
| 0 | 表头左列 | 左(2) | -1447425 | 有 | SimSun 80 | 第一列表头 |
| 1 | 表头 | 左(2) | -1447425 | 有 | 宋体 80 | 普通表头 |
| 2 | 数据 | 左(2) | 无 | 有 | SimSun 80 | 数据单元格 |
| 3 | 金额 | 右(4) | -1 | 有 | SimSun 80 + 前景色 -8163329 | 金额/数值 |
| 4 | 默认 | 中(0) | 无 | 无 | simhei 72 | 默认样式 |

### 颜色值（Java 有符号 32 位整数）

| 颜色 | RGB | 十进制值 | 用途 |
|------|-----|----------|------|
| 白色 | (255,255,255) | -1 | 纯白背景 |
| 表头背景 | (233,233,255) | -1447425 | 表头背景色 |
| 边框灰 | (218,226,246) | -2432266 | 边框颜色 |
| 金额蓝 | (0,102,204) | -8163329 | 金额字体颜色 |

### 样式 XML 示例

```xml
<Style style_name="表头" horizontal_alignment="2" imageLayout="1">
    <FRFont name="宋体" style="0" size="80"/>
    <Background name="ColorBackground">
        <color>
            <FineColor color="-1447425" hor="-1" ver="-1"/>
        </color>
    </Background>
    <Border>
        <Top style="1"><color><FineColor color="-2432266" hor="-1" ver="-1"/></color></Top>
        <Bottom style="1"><color><FineColor color="-2432266" hor="-1" ver="-1"/></color></Bottom>
        <Left style="1"><color><FineColor color="-2432266" hor="-1" ver="-1"/></color></Left>
        <Right style="1"><color><FineColor color="-2432266" hor="-1" ver="-1"/></color></Right>
    </Border>
</Style>
```

## 六、数据源参数绑定规则

**核心原则：数据源参数只能多不能少**

```
筛选组件 codes: [startDate, endDate, orgId]
数据源参数: {startDate: "", endDate: "", orgId: "", region: ""}

✅ 校验通过：
  - startDate → 有对应筛选组件
  - endDate → 有对应筛选组件
  - orgId → 有对应筛选组件
  - region → 多余参数，不影响（只多不少）

筛选组件 codes: [startDate, endDate]
数据源参数: {startDate: "", orgId: ""}

❌ 校验失败：
  - orgId → 无对应筛选组件，无默认值
  - endDate → 筛选组件有但数据源参数没有
```

## 七、动态列功能

当用户需要可选择显示/隐藏列时：

1. 筛选区域最后一行添加 ComboCheckBox，参数名固定为 `cols`
2. 选项为所有表头名称
3. 默认值为全部表头（逗号分隔）
4. 每列表头添加条件属性：`INARRAY('表头名称',$cols) = 0` → 列宽=0

## 八、生成 CPT 检查清单

| 检查项 | 要求 |
|--------|------|
| ClassTableData Parameters | 必须存在 |
| `<O>` 标签格式 | 必须 `<![CDATA[]]>` |
| 参数名绑定 | 筛选组件 code = 数据源参数名 |
| 样式索引 | 不超出 StyleList 范围 |
| XML 属性值 | 全部为字符串类型 |
| FineColor | 必须有 `hor="-1"` 和 `ver="-1"` |
| RowHeight/ColumnWidth | 使用 CDATA 格式 |
| 筛选组件位置 | 按布局规范计算，不能重叠 |

## 九、常用 Java Class 数据源

```
# 明细数据
com.yocyl.fr.engine.tableData.finance.CreditContractDetailData

# 统计数据
com.yocyl.fr.engine.tableData.finance.CreditContractStatisticData
com.yocyl.fr.engine.tableData.finance.CreditContractUserOrgStatisticData
com.yocyl.fr.engine.tableData.finance.CreditProductStatisticData
```
