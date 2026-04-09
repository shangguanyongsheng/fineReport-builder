# FineReport Builder 核心代码说明

> 关键代码文件详解，方便快速理解和问题排查

---

## 一、核心文件概览

| 文件 | 职责 | 重要程度 |
|------|------|----------|
| `parsers/cpt_generator.py` | CPT 文件生成器 | ⭐⭐⭐ 核心 |
| `web/app.py` | Web 服务入口 | ⭐⭐⭐ 入口 |
| `web/templates/excel_convert_v3.html` | V3 界面 | ⭐⭐ 交互 |
| `parsers/cpt_parser.py` | CPT 解析器 | ⭐ 辅助 |
| `parsers/class_table_data.py` | ClassTableData 解析 | ⭐ 辅助 |

---

## 二、数据流转流程图

### 2.1 整体架构流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    excel_convert_v3.html                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Excel上传│ │数据源配置│ │ 列映射   │ │筛选组件  │ │ 样式选择 │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │   │
│  │       │            │            │            │            │         │   │
│  │       ▼            ▼            ▼            ▼            ▼         │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              collectConfig() 收集配置数据                    │   │   │
│  │  │  {datasources, column_mapping, filter_components, styles}   │   │   │
│  │  └─────────────────────────┬───────────────────────────────────┘   │   │
│  └────────────────────────────┼───────────────────────────────────────┘   │
└───────────────────────────────┼───────────────────────────────────────────┘
                                │
                                │ POST /api/v2/generate
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              后端处理层                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         web/app.py                                  │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐  │   │
│  │  │ 参数处理         │    │ 列映射处理       │    │ 筛选组件处理  │  │   │
│  │  │                  │    │                  │    │               │  │   │
│  │  │ parameter_template│   │ column_mapping   │    │filter_components│ │   │
│  │  │     ↓            │    │     ↓            │    │     ↓         │  │   │
│  │  │ 解析默认值       │    │ 构建单元格配置   │    │ 构建控件配置  │  │   │
│  │  │ 处理JSON字符串   │    │ 表头+数据行      │    │ Label+Input   │  │   │
│  │  └────────┬─────────┘    └────────┬─────────┘    └───────┬───────┘  │   │
│  │           │                       │                      │          │   │
│  │           └───────────────────────┼──────────────────────┘          │   │
│  │                                   ▼                                 │   │
│  │                    ┌──────────────────────────┐                     │   │
│  │                    │   构建 cpt_config 对象   │                     │   │
│  │                    │  {title, data_sources,  │                     │   │
│  │                    │   cells, filter_controls,│                     │   │
│  │                    │   styles, ...}          │                     │   │
│  │                    └───────────┬──────────────┘                     │   │
│  └────────────────────────────────┼────────────────────────────────────┘   │
└───────────────────────────────────┼────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CPT生成层                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    parsers/cpt_generator.py                         │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    generate(config)                          │   │   │
│  │  │                                                              │   │   │
│  │  │  1. 创建 WorkBook 根节点                                     │   │   │
│  │  │  2. _generate_table_data_map()  → TableDataMap              │   │   │
│  │  │  3. _generate_report_web_attr() → ReportWebAttr             │   │   │
│  │  │  4. _generate_report()           → Report (单元格)          │   │   │
│  │  │  5. _generate_parameter_attr()   → ReportParameterAttr      │   │   │
│  │  │  6. _generate_style_list()       → StyleList               │   │   │
│  │  │  7. _prettify()                  → XML格式化+CDATA转换      │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              输出层                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         outputs/*.cpt                                │   │
│  │                                                                      │   │
│  │  <?xml version="1.0" encoding="UTF-8"?>                             │   │
│  │  <WorkBook xmlVersion="20211223" releaseVersion="11.5.0">           │   │
│  │    <TableDataMap>...</TableDataMap>                                 │   │
│  │    <ReportWebAttr>...</ReportWebAttr>                               │   │
│  │    <Report>...</Report>                                             │   │
│  │    <ReportParameterAttr>...</ReportParameterAttr>                   │   │
│  │    <StyleList>...</StyleList>                                       │   │
│  │  </WorkBook>                                                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Class 数据源参数处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Class 数据源参数处理流程                                  │
└─────────────────────────────────────────────────────────────────────────────┘

前端输入 (parameter_template)
         │
         │  [{"orgId": ""}, {"startDate": ""}, {"indexInfo": {"fieldCode": "repay.id"}}]
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  web/app.py - 参数解析                                                       │
│                                                                              │
│  for item in param_template:                                                 │
│      for param_name, param_value in item.items():                           │
│          │                                                                   │
│          ├─ 空值 ("")    → {'name': name, 'default': ''}                    │
│          │                 (从筛选组件获取)                                   │
│          │                                                                   │
│          ├─ 简单值       → {'name': name, 'default': str(value)}            │
│          │                                                                   │
│          └─ JSON值       → {'name': name, 'default': json.dumps(value)}     │
│                            (转成JSON字符串作为默认值)                          │
│                                                                              │
│  params = [{'name': 'orgId', 'default': ''},                                │
│            {'name': 'startDate', 'default': ''},                            │
│            {'name': 'indexInfo', 'default': '{"fieldCode":"repay.id"}'}]    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  cpt_generator.py - XML生成                                                  │
│                                                                              │
│  <TableData name="..." class="com.fr.data.impl.ClassTableData">             │
│    <Parameters>                                                             │
│      <Parameter>                                                            │
│        <Attributes name="orgId"/>                                           │
│        <O><![CDATA[]]></O>                    ← 空值，从筛选组件获取         │
│      </Parameter>                                                           │
│      <Parameter>                                                            │
│        <Attributes name="startDate"/>                                       │
│        <O><![CDATA[]]></O>                    ← 空值，从筛选组件获取         │
│      </Parameter>                                                           │
│      <Parameter>                                                            │
│        <Attributes name="indexInfo"/>                                       │
│        <O><![CDATA[{"fieldCode":"repay.id"}]]></O>  ← 有默认值，写死        │
│      </Parameter>                                                           │
│    </Parameters>                                                            │
│    <ClassTableDataAttr className="com.xxx.DataClass"/>                      │
│  </TableData>                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 XML格式化与CDATA转换流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     _prettify() XML格式化流程                                 │
└─────────────────────────────────────────────────────────────────────────────┘

ET.Element → XML字符串
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  minidom.toprettyxml() 格式化                                                │
│                                                                              │
│  问题：Python XML库会自动转义特殊字符                                         │
│        {"fieldCode": "repay.id"} → {"fieldCode": &quot;repay.id&quot;}    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CDATA 转义还原                                                              │
│                                                                              │
│  result.replace('&lt;![CDATA[', '<![CDATA[')                                │
│  result.replace(']]&gt;', ']]>')                                            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  O标签 CDATA 格式转换（帆软兼容性要求）                                        │
│                                                                              │
│  1. <O/> → <O><![CDATA[]]></O>                                              │
│  2. <O></O> → <O><![CDATA[]]></O>                                           │
│  3. <O>value</O> → <O><![CDATA[value]]></O>                                 │
│                                                                              │
│  ⚠️ 关键：使用 html.unescape() 反转义 XML 实体                               │
│     否则 JSON字符串中的 &quot; 无法正确显示                                   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                           最终 CPT XML 文件
```

---

## 三、cpt_generator.py 核心生成器

### 3.1 文件结构

```python
class CPTGenerator:
    """CPT 文件生成器"""

    # 核心方法
    def generate(config) -> str          # 生成完整 CPT
    def _generate_table_data_map()       # 生成数据源映射
    def _generate_report()               # 生成报表主体
    def _generate_parameter_attr()       # 生成参数面板
    def _generate_style_list()           # 生成样式列表
    def _prettify()                      # XML 格式化

    # 辅助方法
    def _generate_cell()                 # 生成单元格
    def _generate_widget()               # 生成控件
    def _create_style_element()          # 创建样式元素
    def _get_default_styles()            # 获取默认样式
```

### 3.2 generate() 主流程

```python
def generate(self, config: Dict[str, Any]) -> str:
    """生成 .cpt 文件内容

    输入配置结构:
    {
        'title': '报表标题',
        'sheet_name': 'Sheet1',
        'data_sources': [...],      # 数据源列表
        'filter_controls': [...],   # 筛选控件列表
        'cells': [...],             # 单元格列表
        'styles': [...]             # 样式列表
    }

    输出: CPT XML 字符串
    """
    # 1. 创建根节点
    root = ET.Element('WorkBook')

    # 2. 生成各模块（按帆软 CPT 结构顺序）
    root.append(self._generate_table_data_map(data_sources))   # 数据源
    root.append(self._generate_report_web_attr(config))        # Web属性
    root.append(self._generate_report(config))                  # 报表主体
    root.append(self._generate_parameter_attr(filter_controls)) # 参数面板
    root.append(self._generate_style_list(styles))              # 样式列表

    # 3. 格式化输出
    return self._prettify(root)
```

### 3.3 _generate_table_data_map() 数据源生成

**关键点：ClassTableData 参数处理**

```python
def _generate_table_data_map(self, data_sources):
    for ds in data_sources:
        # ⭐ 关键：ClassTableData 必须有 Parameters 节点
        is_class_table_data = ds.get('type') == 'ClassTableData'

        if 'parameters' in ds or is_class_table_data:
            params = ds.get('parameters', [])
            params_elem = ET.SubElement(table_data, 'Parameters')

            for param in params:
                param_elem = ET.SubElement(params_elem, 'Parameter')
                attr = ET.SubElement(param_elem, 'Attributes')
                attr.set('name', param.get('name', ''))

                # ⭐ 关键：使用 CDATA 格式
                default = ET.SubElement(param_elem, 'O')
                default.text = param.get('default', '')

        # ClassTableData 特有：Java 类名
        if ds.get('class_name'):
            class_attr = ET.SubElement(table_data, 'ClassTableDataAttr')
            class_attr.set('className', ds['class_name'])
```

### 3.4 _generate_parameter_attr() 参数面板生成

**关键点：控件布局计算**

```python
def _generate_parameter_attr(self, controls):
    # 布局规范（固定值，勿改）
    LABEL_WIDTH = 89       # Label 宽度
    INPUT_WIDTH = 135      # 输入控件宽度
    LABEL_INPUT_GAP = 4    # Label 与输入框间距
    PAIR_GAP = 4           # 同一行组件对间距（统一4px）
    ROW_GAP = 8            # 行间距
    ROW_HEIGHT = 28        # 控件高度
    PAIRS_PER_ROW = 5      # 每行组件对数
    START_X = 10           # 起始 X 坐标
    START_Y = 10           # 起始 Y 坐标

    for i, ctrl in enumerate(controls):
        row = i // PAIRS_PER_ROW
        col = i % PAIRS_PER_ROW

        # 每对总宽度
        pair_width = LABEL_WIDTH + LABEL_INPUT_GAP + INPUT_WIDTH
        pair_start_x = START_X + col * (pair_width + PAIR_GAP)
        pair_start_y = START_Y + row * (ROW_HEIGHT + ROW_GAP)
```

### 3.5 _prettify() XML 格式化

**关键点：CDATA 格式转换 + XML实体反转义**

```python
def _prettify(self, elem):
    # 格式化 XML
    dom = minidom.parseString(rough_string)
    pretty = dom.toprettyxml(indent='', encoding=None)

    # 处理 CDATA 转义还原
    result = result.replace('&lt;![CDATA[', '<![CDATA[')
    result = result.replace(']]&gt;', ']]>')

    # ⭐ 帆软兼容性：O 标签必须用 CDATA 格式
    result = re.sub(r'<O\s*/>', '<O>\n<![CDATA[]]></O>', result)
    result = re.sub(r'<O></O>', '<O>\n<![CDATA[]]></O>', result)

    # 处理有值的 O 标签
    def replace_o_tag(match):
        content = match.group(1)
        if 'CDATA' in content:
            return match.group(0)

        # ⭐ 关键：反转义 XML 实体（JSON字符串中的特殊字符）
        import html
        content = html.unescape(content)

        return f'<O>\n<![CDATA[{content}]]></O>'

    # 使用 .*? 匹配可能包含转义实体的内容
    result = re.sub(r'<O>(.*?)</O>', replace_o_tag, result)
    return result
```

---

## 四、web/app.py Web 服务

### 4.1 核心路由

```python
# 页面路由
@app.route('/excel-convert-v3')      # V3 界面

# API 路由
@app.route('/api/v2/generate')       # 报表生成 API ⭐ 核心
@app.route('/api/analyze/cpt')       # CPT 分析
@app.route('/api/download/<file>')   # 文件下载
```

### 4.2 generate_report_v2() 参数处理

**关键点：参数默认值处理**

```python
if datasource.get('type') == 'class':
    param_template = datasource.get('parameter_template', [])
    params = []

    if param_template:
        for item in param_template:
            if isinstance(item, dict):
                for param_name, param_value in item.items():
                    # 处理默认值
                    if param_value == '' or param_value is None:
                        # 空值：从筛选组件获取
                        params.append({'name': param_name, 'default': ''})
                    elif isinstance(param_value, (dict, list)):
                        # ⭐ 复杂JSON：转成 JSON 字符串作为默认值
                        params.append({'name': param_name,
                                      'default': json.dumps(param_value, ensure_ascii=False)})
                    else:
                        # 简单值：直接作为默认值
                        params.append({'name': param_name, 'default': str(param_value)})
    else:
        # ⭐ 自动从 filter_components 推断参数
        for comp in filter_components:
            code = comp.get('code')
            if code:
                params.append({'name': code, 'default': ''})
```

---

## 五、常见问题修复

### 5.1 参数为空

**原因**：
1. 前端未传 `parameter_template`
2. 后端未自动推断参数
3. 生成器未创建 `<Parameters>` 节点

**修复**：
```python
# web/app.py - 自动推断
if not param_template:
    for comp in filter_components:
        params.append({'name': comp['code'], 'default': ''})

# cpt_generator.py - 必须生成 Parameters
if 'parameters' in ds or is_class_table_data:
    params_elem = ET.SubElement(table_data, 'Parameters')
```

### 5.2 CDATA 格式缺失

**原因**：`<O/>` 自闭合标签帆软不识别

**修复**：
```python
# cpt_generator.py - _prettify()
result = re.sub(r'<O\s*/>', '<O>\n<![CDATA[]]></O>', result)
```

### 5.3 样式颜色错误

**原因**：颜色值计算错误

**修复**：
```python
# 正确的颜色值
HEADER_BG = '-1447425'   # RGB(233,233,255)，不是 -16771561
BORDER_COLOR = '-2432266' # RGB(218,226,246)
```

### 5.4 FineColor 属性缺失

**原因**：缺少 `hor` 和 `ver` 属性

**修复**：
```python
fine_color.set('color', str(color_value))
fine_color.set('hor', '-1')  # 必须添加
fine_color.set('ver', '-1')  # 必须添加
```

### 5.5 ⭐ Class 入参 JSON 默认值丢失

**原因**：
1. JSON 默认值如 `{"fieldCode": "repay.id"}` 被 XML 转义成 `{"fieldCode": &quot;repay.id&quot;}`
2. 原正则 `<O>([^<]*)</O>` 无法匹配包含 `&lt;` 等转义实体的内容
3. 导致默认值在 CDATA 转换时丢失

**修复**：
```python
# cpt_generator.py - _prettify()

# 1. 正则改为 .*? 匹配任意内容（包括转义实体）
result = re.sub(r'<O>(.*?)</O>', replace_o_tag, result)

# 2. 使用 html.unescape() 反转义 XML 实体
import html
content = html.unescape(content)

# 3. 确保 JSON 字符串正确放入 CDATA
return f'<O>\n<![CDATA[{content}]]></O>'
```

**验证方法**：
```python
# 测试用例
param_value = {"fieldCode": "repay.id"}
default = json.dumps(param_value)  # '{"fieldCode": "repay.id"}'

# 生成的 XML 应为：
# <O><![CDATA[{"fieldCode": "repay.id"}]]></O>
# 而不是：
# <O><![CDATA[{"fieldCode": &quot;repay.id&quot;}]]></O>
```

---

## 六、调试技巧

### 6.1 打印生成的 XML

```python
from parsers.cpt_generator import CPTGenerator

generator = CPTGenerator()
cpt_content = generator.generate(config)

# 打印关键部分
import re
match = re.search(r'<TableDataMap>.*?</TableDataMap>', cpt_content, re.DOTALL)
print(match.group(0))
```

### 6.2 对比原始模板

```bash
# 查看原始模板结构
grep -A 10 "ClassTableData" templates/FinanceCreditContractAnalysis.cpt

# 比较生成的文件
diff outputs/report.cpt templates/FinanceCreditContractAnalysis.cpt
```

### 6.3 日志级别

```python
# app.py 中添加详细日志
logger.info(f"参数: {params}")
logger.info(f"筛选组件: {filter_components}")
logger.info(f"单元格数量: {len(cpt_config['cells'])}")
```

---

## 七、代码修改检查清单

修改代码后，检查以下内容：

- [ ] ClassTableData 是否有 `<Parameters>` 节点？
- [ ] `<O>` 标签是否使用 CDATA 格式？
- [ ] FineColor 是否有 `hor` 和 `ver` 属性？
- [ ] 表头背景色是否为 `-1447425`？
- [ ] 边框颜色是否为 `-2432266`？
- [ ] 控件位置计算是否正确（同一行间距统一4px）？
- [ ] 参数名是否与筛选组件 code 一致？
- [ ] JSON 默认值是否正确反转义？

---

_📅 文档更新日期: 2026-04-09_