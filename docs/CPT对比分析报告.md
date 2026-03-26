# CPT 文件对比分析报告

## 对比文件

| 文件 | 大小 | 说明 |
|------|------|------|
| 生成的报表 | 3.9KB | 授信合同报-明细_20260326_175611.cpt |
| 原始报表 | 148KB | FinanceCreditContractAnalysis.cpt |

## 主要差异

### 1. 样式配置 (StyleList)

**生成的报表** - 只有 1 个默认样式：
```xml
<StyleList>
  <Style style_name="默认">
    <FRFont name="simhei" style="0" size="72"/>
    <Background name="NullBackground"/>
  </Style>
</StyleList>
```

**原始报表** - 有多个样式：
```xml
<StyleList>
  <Style style_name="标题样式">
    <FRFont name="宋体" style="0" size="96">  <!-- 加粗 -->
      <FRFontColor color="#000000"/>
    </FRFont>
    <Background name="ColorBackground">
      <Color value="#E6F7FF"/>  <!-- 浅蓝色背景 -->
    </Background>
    <Border>
      <Top style="thin" color="#000000"/>
      <Bottom style="thin" color="#000000"/>
      <Left style="thin" color="#000000"/>
      <Right style="thin" color="#000000"/>
    </Border>
  </Style>
  
  <Style style_name="数据样式">
    <FRFont name="SimSun" style="0" size="80"/>
    <Background name="NullBackground"/>
    <Border>...</Border>
  </Style>
</StyleList>
```

**需要支持的样式配置：**
```json
{
  "styles": [
    {
      "name": "标题样式",
      "font": {
        "name": "宋体",
        "size": 96,
        "bold": true,
        "color": "#000000"
      },
      "background": "#E6F7FF",
      "border": {
        "top": {"style": "thin", "color": "#000000"},
        "bottom": {"style": "thin", "color": "#000000"},
        "left": {"style": "thin", "color": "#000000"},
        "right": {"style": "thin", "color": "#000000"}
      },
      "alignment": {
        "horizontal": "center",
        "vertical": "center"
      }
    }
  ]
}
```

---

### 2. 单元格数据绑定

**生成的报表** - 只有静态文本：
```xml
<C c="0" r="0">
  <O>序号</O>
</C>
```

**原始报表** - 支持数据绑定和扩展：
```xml
<C c="1" r="1" s="2">
  <O t="DSColumn">
    <Attributes dsName="CreditContractDetailData" columnName="id"/>
  </O>
  <Expand dir="0"/>  <!-- 纵向扩展 -->
</C>
```

**需要支持的数据绑定配置：**
```json
{
  "cells": [
    {
      "column": 0,
      "row": 0,
      "value": "序号",
      "style_index": 0
    },
    {
      "column": 1,
      "row": 1,
      "value_type": "DSColumn",
      "datasource": "CreditContractDetailData",
      "column_name": "id",
      "style_index": 2,
      "expand_dir": 0  // 0=纵向扩展
    }
  ]
}
```

---

### 3. 合并单元格

**原始报表**：
```xml
<C c="0" r="0" rs="6" s="0">  <!-- rs="6" 表示合并6行 -->
  <O>...</O>
</C>
```

**需要支持的合并配置：**
```json
{
  "cells": [
    {
      "column": 0,
      "row": 0,
      "row_span": 6,
      "col_span": 1,
      "value": "标题"
    }
  ]
}
```

---

### 4. 参数面板

**原始报表** - 完整的参数面板：
- LabelName 标签
- 多种控件类型
- 位置布局

**生成的报表** - 基础参数面板：
- 缺少 LabelName 标签显示
- 需要优化布局

---

## 改进方案

### 1. 样式 JSON 配置

在 Step 5 添加样式配置：

```json
{
  "styles": [
    {
      "name": "表头样式",
      "font": {"name": "宋体", "size": 12, "bold": true},
      "background": "#E6F7FF",
      "border": "all",
      "alignment": "center"
    },
    {
      "name": "数据样式",
      "font": {"name": "SimSun", "size": 10},
      "border": "all",
      "alignment": "left"
    },
    {
      "name": "金额样式",
      "font": {"name": "SimSun", "size": 10},
      "border": "all",
      "alignment": "right",
      "number_format": "#,##0.00"
    }
  ]
}
```

### 2. 数据绑定配置

在列映射中添加数据绑定选项：

```json
{
  "column_mapping": {
    "A": {
      "field": "contractNo",
      "style": "数据样式",
      "bind_data": true,
      "expand": true
    },
    "B": {
      "field": "contractName",
      "style": "数据样式",
      "bind_data": true
    }
  }
}
```

### 3. 模板样式

提供预设样式模板：

| 模板 | 说明 |
|------|------|
| `simple` | 简洁样式 |
| `finance` | 财务报表样式 |
| `list` | 列表样式 |

---

## 实现优先级

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 样式 JSON 配置 | 支持自定义样式 |
| P0 | 数据绑定 | 单元格绑定数据源字段 |
| P1 | 扩展方向 | 纵向/横向扩展 |
| P1 | 边框配置 | 全边框/无边框等 |
| P2 | 合并单元格 | rowspan/colspan |
| P2 | 数字格式 | 金额、百分比等 |
| P3 | 条件格式 | 根据值变化样式 |