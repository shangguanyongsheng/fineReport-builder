# Agent 长期记忆

**创建时间**: 2026-03-27
**最后更新**: 2026-03-27

---

## 模板知识库

### 管理分析报表

**文件**: `templates/FinanceCreditContractAnalysis.cpt`

#### 筛选区域
- 位置: `ReportParameterAttr > ParameterUI > Layout`
- 布局: 每行 5 对组件（Label + 输入控件）
- 控件间距: 待解析
- 现有组件: 10 对 (Label + 输入)

#### 数据区域
- 表头行: row=0
- 数据行: row=1
- 样式: 待解析

#### 数据源
- 类型: Class
- 数量: 15 个数据源
- 主要数据源: CreditContractDetailData

---

### 明细报表

**文件**: `templates/FinanceCreditContractAnalysisDetail.cpt`

> 待解析

---

## 错误教训

### 2026-03-27: 样式序列化失败
- **错误**: `cannot serialize 14 (type int)`
- **原因**: XML 属性值必须是字符串类型
- **解决**: 所有数值用 `str()` 转换后再设置
- **代码位置**: `parsers/cpt_generator.py`

### 2026-03-27: Label 控件缺失
- **问题**: 筛选区域只有输入控件，没有 Label 标签
- **原因**: 只设置了 LabelName 属性，没有生成独立 Label 控件
- **解决**: 每个输入控件前生成独立的 Label 控件
- **代码位置**: `parsers/cpt_generator.py:_generate_parameter_attr`

---

## 成功模式

### 模板修改流程

```
1. 加载模板 → 解析 XML 结构
2. 定位筛选区域 → 读取现有组件
3. 对比用户需求 → 计算增删改
4. 执行修改 → 调整布局位置
5. 验证输出 → XML 格式检查
```

### 样式模板

| 索引 | 名称 | 对齐 | 背景 | 用途 |
|------|------|------|------|------|
| 0 | 表头左列 | 左 | 蓝 | 第一列表头 |
| 1 | 表头 | 左 | 蓝 | 普通表头 |
| 2 | 数据 | 左 | 无 | 普通数据 |
| 3 | 金额 | 右 | 白 | 金额字段 |
| 4 | 默认 | 中 | 无 | 默认样式 |

---

## 组件知识

### Label 控件

```xml
<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
  <InnerWidget class="com.fr.form.ui.Label">
    <WidgetName name="label_0"/>
    <widgetValue>
      <O>标签文本</O>
    </widgetValue>
  </InnerWidget>
  <BoundsAttr x="10" y="10" width="70" height="28"/>
</Widget>
```

### 输入控件

```xml
<Widget class="com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget">
  <InnerWidget class="com.fr.form.ui.DateEditor">
    <WidgetName name="startDate"/>
  </InnerWidget>
  <BoundsAttr x="90" y="10" width="135" height="28"/>
</Widget>
```

---

## 数据源配置

### Class 数据源

```json
{
  "name": "credit_data",
  "type": "ClassTableData",
  "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
  "parameters": [
    {"name": "orgId", "default": ""},
    {"name": "startDate", "default": ""},
    {"name": "endDate", "default": ""}
  ]
}
```

### 数据库数据源

```json
{
  "name": "sales_data",
  "type": "DBTableData",
  "database": "cfs-report",
  "sql": "SELECT * FROM table WHERE id = ${id}",
  "parameters": [
    {"name": "id", "default": ""}
  ]
}
```

---

_此文件由 Agent 自动维护，记录学习和进化过程_