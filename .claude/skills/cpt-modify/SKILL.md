---
name: cpt-modify
description: 基于现有 CPT 模板进行修改。支持增删筛选组件、修改数据列、更新数据源参数等操作。使用 XML 节点复制方式保持所有默认配置不变。
type: tool

---

# CPT 修改技能

## 触发条件

用户要求修改一个已有的 `.cpt` 文件，例如：
- "增加/删除筛选条件"
- "修改数据列"
- "更换数据源"
- "调整字段映射"

## 执行流程

### Step 1: 分析现有 CPT 结构

```bash
# 解析现有 CPT 文件，输出结构摘要
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('文件路径')
root = tree.getroot()

# 数据源
for td in root.findall('.//TableData'):
    print(f'数据源: {td.get(\"name\")} ({td.get(\"class\")})')
    for p in td.findall('.//Parameter/Attributes'):
        print(f'  参数: {p.get(\"name\")}')

# 筛选组件
for wn in root.findall('.//WidgetName'):
    name = wn.get('name', '')
    if name and not name.startswith('label_') and name != 'para':
        print(f'筛选组件: {name}')

# 单元格数量
cells = root.findall('.//CellElementList/C')
print(f'单元格总数: {len(cells)}')
"
```

### Step 2: 确定修改操作

根据用户需求确定操作类型：

| 操作 | 策略 |
|------|------|
| 增加筛选组件 | 复制现有同类型控件 XML 节点，修改 name/label/position |
| 删除筛选组件 | 定位并移除对应 Widget 节点 |
| 增加数据列 | 复制最后列的单元格，修改列索引和字段名 |
| 删除数据列 | 移除该列索引的所有单元格 |
| 修改数据源 | 更新 TableData 节点的 class_name/parameters |
| 修改字段映射 | 更新 DSColumn 的 columnName 属性 |

### Step 3: 执行修改

#### 增加筛选组件

```python
import xml.etree.ElementTree as ET
import copy

tree = ET.parse(cpt_path)
root = tree.getroot()

# 找到参数面板布局
layout = root.find('.//ReportParameterAttr//Layout')

# 复制一个现有同类型控件作为模板
template = root.find(".//InnerWidget[@class='com.fr.form.ui.DateEditor']/..")
# 或者从模板文件复制

new_widget = copy.deepcopy(template)
# 只修改必要属性：
# 1. WidgetName → 新的 code
# 2. 显示文本 → 新的 label
# 3. BoundsAttr → 新位置

layout.append(new_widget)
```

#### 修改数据列

```python
cell_list = root.find('.//CellElementList')

# 清空旧数据（删除 row >= 0 的所有单元格）
for cell in list(cell_list):
    r = int(cell.get('r', 0))
    cell_list.remove(cell)

# 重新生成表头和数据行
for i, col in enumerate(new_columns):
    # 表头
    header = ET.Element('C')
    header.set('c', str(i))
    header.set('r', '0')
    header.set('s', '1')
    o = ET.SubElement(header, 'O')
    o.text = col['header']
    cell_list.append(header)
    
    # 数据行
    data = ET.Element('C')
    data.set('c', str(i))
    data.set('r', '1')
    data.set('s', '3' if col.get('is_amount') else '2')
    o = ET.SubElement(data, 'O')
    o.set('t', 'DSColumn')
    attrs = ET.SubElement(o, 'Attributes')
    attrs.set('dsName', data_source_name)
    attrs.set('columnName', col['field'])
    cell_list.append(data)
```

#### 更新数据源参数

```python
table_data_map = root.find('.//TableDataMap')
for td in table_data_map.findall('TableData'):
    if td.get('name') == target_ds_name:
        params_elem = td.find('Parameters')
        # 清除旧参数
        for p in list(params_elem):
            params_elem.remove(p)
        # 添加新参数
        for param in new_params:
            p = ET.SubElement(params_elem, 'Parameter')
            attrs = ET.SubElement(p, 'Attributes')
            attrs.set('name', param['name'])
            o = ET.SubElement(p, 'O')
            o.text = param.get('default', '')
```

### Step 4: 重新计算筛选组件位置

```python
LABEL_WIDTH = 89
INPUT_WIDTH = 135
LABEL_INPUT_GAP = 4
PAIR_GAP = 4
ROW_HEIGHT = 28
ROW_GAP = 8
PAIRS_PER_ROW = 5
START_X = 10
START_Y = 10

widgets = layout.findall('Widget')
# 过滤掉 label_ 开头的和 para
input_widgets = [w for w in widgets
    if w.find('.//WidgetName')
    and not w.find('.//WidgetName').get('name', '').startswith('label_')
    and w.find('.//WidgetName').get('name') != 'para']

for i, widget in enumerate(input_widgets):
    row = i // PAIRS_PER_ROW
    col = i % PAIRS_PER_ROW
    pair_width = LABEL_WIDTH + LABEL_INPUT_GAP + INPUT_WIDTH
    input_x = START_X + col * (pair_width + PAIR_GAP) + LABEL_WIDTH + LABEL_INPUT_GAP
    y = START_Y + row * (ROW_HEIGHT + ROW_GAP)
    
    bounds = widget.find('BoundsAttr')
    if bounds is not None:
        bounds.set('x', str(input_x))
        bounds.set('y', str(y))
    
    # 同时更新对应的 Label
    label_index = i * 2  # label 在 input 前面
    if label_index < len(widgets):
        label_bounds = widgets[label_index].find('BoundsAttr')
        if label_bounds:
            label_bounds.set('x', str(START_X + col * (pair_width + PAIR_GAP)))
            label_bounds.set('y', str(y))
```

### Step 5: 保存

```python
tree.write(output_path, encoding='UTF-8', xml_declaration=True)
```

## 修改操作检查清单

| 操作 | 需要检查 |
|------|----------|
| 增加筛选组件 | 位置不重叠、code 不重复 |
| 删除筛选组件 | 数据源参数是否还有对应组件 |
| 增加数据列 | style_index 有效、DSColumn 绑定正确 |
| 删除数据列 | 删除该列所有单元格（表头+数据） |
| 修改数据源 | ClassTableData 的 Parameters 必须存在 |
| 修改参数 | 空值参数有对应筛选组件 |

## 参数绑定校验

修改完成后必须运行校验：

```
筛选组件 codes = {所有非 label_ 的 WidgetName}
数据源参数 = {ClassTableData 中所有 Parameters/Attributes/@name}

对于每个参数:
  if 参数值 == "" and 参数名 not in 筛选组件:
    ⚠️ 警告: 参数 '{参数名}' 无对应筛选组件
```

## 工具脚本

使用 `cpt_tools/generate.py` 的 `--modify` 模式：

```bash
python cpt_tools/generate.py \
  --modify outputs/existing.cpt \
  --add-filters '[{"label":"区域","code":"region","type":"ComboBox"}]' \
  --add-columns '[{"header":"区域","field":"region"}]' \
  --output outputs/modified.cpt
```
