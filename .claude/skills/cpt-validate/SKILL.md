---
name: cpt-validate
description: 验证 CPT 文件是否符合帆软规范。检查 XML 结构、参数绑定、样式索引、CDATA 格式等。用于生成报表后的自测环节。
type: tool

---

# CPT 验证技能

## 触发条件

用户要求检查或验证一个 `.cpt` 文件，或在生成/修改报表后自动执行。

## 检查项

### 1. XML 结构完整性

```python
import xml.etree.ElementTree as ET

def check_structure(root):
    issues = []
    
    # 必需根节点
    if root.tag != 'WorkBook':
        issues.append(f"❌ 根节点应为 WorkBook，实际为 {root.tag}")
    
    # 必需子节点
    required = ['TableDataMap', 'Report', 'ReportParameterAttr', 'StyleList']
    for tag in required:
        if root.find(tag) is None:
            issues.append(f"❌ 缺少必需节点: {tag}")
    
    return issues
```

### 2. ClassTableData 参数检查

```python
def check_class_table_params(root):
    issues = []
    
    for td in root.findall('.//TableData[@class="com.fr.data.impl.ClassTableData"]'):
        name = td.get('name')
        params = td.find('Parameters')
        
        if params is None:
            issues.append(f"❌ [{name}] 缺少 <Parameters> 节点")
        elif len(params.findall('Parameter')) == 0:
            issues.append(f"⚠️ [{name}] Parameters 为空")
        
        # 检查参数的 O 标签 CDATA 格式
        for param in params.findall('Parameter'):
            o = param.find('O')
            if o is None:
                issues.append(f"❌ [{name}] 参数 {param.find('Attributes').get('name')} 缺少 O 标签")
    
    return issues
```

### 3. 筛选组件与数据源参数绑定

```python
def check_filter_binding(root):
    issues = []
    
    # 收集所有筛选组件 code（非 label、非 para 的 WidgetName）
    widget_codes = set()
    for wn in root.findall('.//WidgetName'):
        name = wn.get('name', '')
        if name and not name.startswith('label_') and name != 'para':
            widget_codes.add(name)
    
    # 收集所有 ClassTableData 的空值参数
    for td in root.findall('.//TableData[@class="com.fr.data.impl.ClassTableData"]'):
        ds_name = td.get('name')
        for param in td.findall('.//Parameter'):
            attrs = param.find('Attributes')
            if attrs is None:
                continue
            param_name = attrs.get('name')
            o = param.find('O')
            default = o.text if o is not None else ''
            
            if not default and param_name not in widget_codes:
                issues.append(
                    f"⚠️ [{ds_name}] 参数 '{param_name}' 无对应筛选组件"
                )
    
    return issues
```

### 4. 样式索引范围

```python
def check_style_index(root):
    issues = []
    
    style_count = len(root.findall('.//StyleList/Style'))
    
    for cell in root.findall('.//C[@s]'):
        s = int(cell.get('s'))
        if s >= style_count:
            issues.append(
                f"❌ 单元格(c={cell.get('c')},r={cell.get('r')}) "
                f"样式索引越界: s={s}, 最大={style_count-1}"
            )
    
    return issues
```

### 5. DSColumn 绑定检查

```python
def check_ds_column_binding(root):
    issues = []
    
    # 收集所有数据源名称
    ds_names = set()
    for td in root.findall('.//TableData'):
        ds_names.add(td.get('name'))
    
    # 检查所有 DSColumn 单元格
    for cell in root.findall('.//C'):
        o = cell.find("O[@t='DSColumn']")
        if o is not None:
            attrs = o.find('Attributes')
            if attrs is not None:
                ds_name = attrs.get('dsName', '')
                col_name = attrs.get('columnName', '')
                
                if ds_name and ds_name not in ds_names:
                    issues.append(
                        f"❌ DSColumn 绑定不存在的数据源: {ds_name}"
                    )
                if not col_name:
                    c = cell.get('c')
                    r = cell.get('r')
                    issues.append(
                        f"⚠️ 单元格(c={c},r={r}) DSColumn 未绑定字段名"
                    )
    
    return issues
```

### 6. 筛选组件位置重叠检查

```python
def check_filter_overlap(root):
    issues = []
    
    positions = []
    for widget in root.findall('.//ReportParameterAttr//Layout/Widget'):
        bounds = widget.find('BoundsAttr')
        if bounds is not None:
            x = int(bounds.get('x', 0))
            y = int(bounds.get('y', 0))
            w = int(bounds.get('width', 0))
            h = int(bounds.get('height', 0))
            name = widget.find('.//WidgetName')
            name_text = name.get('name', '') if name is not None else ''
            
            rect = (x, y, x + w, y + h)
            for prev_rect, prev_name in positions:
                if (rect[0] < prev_rect[2] and rect[2] > prev_rect[0] and
                    rect[1] < prev_rect[3] and rect[3] > prev_rect[1]):
                    issues.append(
                        f"⚠️ 控件 '{name_text}' 与 '{prev_name}' 位置重叠"
                    )
            positions.append((rect, name_text))
    
    return issues
```

### 7. CDATA 格式检查（检查 XML 文本而非 DOM）

```python
def check_cdata_format(cpt_text):
    """检查 XML 文本中的 CDATA 格式"""
    import re
    issues = []
    
    # 检查自闭合 O 标签（应该是 CDATA）
    self_close = re.findall(r'<O\s*/>', cpt_text)
    if self_close:
        issues.append(f"❌ 发现 {len(self_close)} 个自闭合 <O/> 标签，应为 CDATA 格式")
    
    # 检查空 O 标签（应该是 CDATA）
    empty_o = re.findall(r'<O></O>', cpt_text)
    if empty_o:
        issues.append(f"❌ 发现 {len(empty_o)} 个空 <O></O> 标签，应为 <![CDATA[]]>")
    
    return issues
```

## 运行验证

### 方式 A：使用 Python 脚本

```bash
cd /home/admin/python-works/fineReport-builder
python cpt_tools/validate.py outputs/report.cpt
```

### 方式 B：内联检查

```bash
python -c "
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0, '.')
from cpt_tools.validate import validate_cpt

result = validate_cpt('outputs/report.cpt')
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

## 验证输出格式

```json
{
  "file": "outputs/report.cpt",
  "valid": true,
  "checks": {
    "structure": {"passed": true, "issues": []},
    "class_table_params": {"passed": true, "issues": []},
    "filter_binding": {"passed": true, "issues": []},
    "style_index": {"passed": true, "issues": []},
    "ds_column_binding": {"passed": true, "issues": []},
    "filter_overlap": {"passed": true, "issues": []},
    "cdata_format": {"passed": true, "issues": []}
  },
  "summary": "✅ 全部检查通过"
}
```

## 自测指令流程

当用户说"自测"或"验证"时，执行：

1. 读取 `outputs/` 目录下最新的 `.cpt` 文件
2. 运行全部 7 项检查
3. 输出结果摘要
4. 如果有 ❌ 错误，列出详细问题并建议修复方案
5. 如果只有 ⚠️ 警告，说明不影响使用但建议关注
