# Agent 长期记忆

**创建时间**: 2026-03-27
**最后更新**: 2026-03-27

---

## 模板知识库

### 管理分析报表

**文件**: `templates/FinanceCreditContractAnalysis.cpt`

#### 筛选区域
- **位置**: `ReportParameterAttr > ParameterUI > Layout`
- **筛选组件**: 10 对 (Label + 输入控件)
- **布局**: 每行 4 对
- **行间距**: 36px

**筛选组件列表**:
| Label | Code | Type |
|-------|------|------|
| 授信类型 | bizType2 | ComboBox |
| 批文/授信 | fine_username9 | TextEditor |
| 额度循环 | financeBankName2 | TextEditor |
| 银行授信机构 | creditProductCode2 | TreeComboBoxEditor |
| 融资品种 | orgId2 | TreeComboBoxEditor |
| 组织标签 | orgTag2 | ComboBox |
| 结束日期结束 | startEndDate2 | DateEditor |
| 结束日期开始 | endStartDate2 | DateEditor |
| 开始日期结束 | startStartDate2 | DateEditor |
| 开始日期开始 | convertCurrencyCode2 | ComboBox |

#### 数据区域
- **表头行**: row=0
- **数据行**: row=1
- **数据源**: 15 个

#### 样式
- 共 5 种样式

---

### 明细报表

**文件**: `templates/FinanceCreditContractAnalysisDetail.cpt`

#### 筛选区域
- **位置**: `ReportParameterAttr > ParameterUI > Layout`
- **筛选组件**: 11 对 (Label + 输入控件)
- **布局**: 每行 4 对
- **行间距**: 36px

**筛选组件列表**:
| Label | Code | Type |
|-------|------|------|
| 授信类型 | bizType | ComboBox |
| 批文/授信 | fine_username9 | TextEditor |
| 被授信人 | orgTag | ComboBox |
| 其他授信机构 | listBoolean | TextEditor |
| 组织标签 | orgId | TreeComboBoxEditor |
| 结束日期止 | startEndDate | DateEditor |
| 开始日期止 | endStartDate | DateEditor |
| 结束日期起 | startStartDate | DateEditor |
| 开始日期起 | convertCurrencyCode | DateEditor |
| 授信状态 | creditProductCode | ComboBox |
| 银行授信机构 | financeBankName | TreeComboBoxEditor |

#### 数据区域
- **表头行**: row=0
- **数据行**: row=1
- **总行数**: 3 行
- **数据源**: 15 个

#### 样式
- 共 6 种样式

---

## 模板对比

| 特性 | 管理分析 | 明细 |
|------|---------|------|
| 筛选组件数 | 10 对 | 11 对 |
| 数据源数 | 15 个 | 15 个 |
| 样式数 | 5 种 | 6 种 |
| 数据行数 | - | 3 行 |

**差异**:
- 明细报表多一个筛选组件
- 明细报表多一种样式

---

## 错误教训

### 2026-03-27: 筛选组件重叠 + 数据列错乱
- **问题1**: 筛选组件位置重叠，同一 Y 坐标下多个控件 X 坐标冲突
- **问题2**: 数据列只更新表头，没有删除旧的数据单元格
- **问题3**: contractNo 字段丢失，Row 1 的 Col 0 没有 DSColumn 绑定
- **原因**: 
  - `recalculate_filter_positions` 只调整现有组件，没有清理多余的
  - `update_data_columns` 使用 modify 模式，没有正确处理列数变化
- **解决**: 
  - 筛选组件使用 `replace` 模式：清空所有 → 重新生成
  - 数据列使用 `replace` 模式：删除所有旧单元格 → 重新生成
- **代码位置**: `agent/core.py`

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

### 2026-03-27: 组件 code 读取错误
- **问题**: Label 控件没有 code 属性导致报错
- **原因**: 遍历组件时假设所有组件都有 code
- **解决**: Label 控件设置 code=None，遍历时检查
- **代码位置**: `agent/core.py:get_filter_components`

---

## 成功模式

### 模板修改流程

```
1. 加载模板 → 解析 XML 结构
2. 定位筛选区域 → 读取现有组件
3. 对比用户需求 → 计算增删改
4. 复制 XML 节点 → 修改必要属性
5. 重新计算位置 → 调整布局
6. 验证输出 → XML 格式检查
```

### 筛选组件增删

```python
# 方式: 复制 XML 节点
new_label = copy.deepcopy(template_label)
new_label_name.set('name', f'label_{code}')
new_label_value.text = label
new_label_bounds.set('x', str(x))

# 重新计算所有组件位置
modifier.recalculate_filter_positions()
```

### 数据列增删

```python
# 多列: 复制最后一个单元格
new_cell = copy.deepcopy(last_cell)
new_cell.set('c', str(new_column_index))

# 少列: 删除多余单元格
cell_list.remove(extra_cell)
```

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
  "parameters": {
    "orgId": "",
    "startDate": "",
    "endDate": ""
  }
}
```

### 参数校验规则

```
数据源参数 vs 筛选组件 code

✅ 有筛选组件 → 绑定
✅ 有默认值 → 使用默认值
❌ 无筛选组件且无默认值 → 错误

原则：数据源参数只能多不能少
```

---

_此文件由 Agent 自动维护，记录学习和进化过程_