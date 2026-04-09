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

## 二、cpt_generator.py 核心生成器

### 2.1 文件结构

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

### 2.2 generate() 主流程

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

### 2.3 _generate_table_data_map() 数据源生成

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

### 2.4 _generate_parameter_attr() 参数面板生成

**关键点：控件布局计算**

```python
def _generate_parameter_attr(self, controls):
    # 布局规范（固定值，勿改）
    LABEL_WIDTH = 89       # Label 宽度
    INPUT_WIDTH = 135      # 输入控件宽度
    LABEL_INPUT_GAP = 4    # Label 与输入框间距
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
        PAIR_GAP = 10
        
        pair_start_x = START_X + col * (pair_width + PAIR_GAP)
        pair_start_y = START_Y + row * (ROW_HEIGHT + ROW_GAP)
        
        # 生成 Label
        label_widget = self._generate_label_widget(...)
        
        # 生成输入控件
        input_widget = self._generate_widget(...)
```

### 2.5 _create_style_element() 样式创建

**关键点：颜色值和 FineColor 属性**

```python
def _create_style_element(self, config):
    style = ET.Element('Style')
    
    # ⭐ 只有默认样式才设置 style_name
    if config.get('is_default'):
        style.set('style_name', config.get('name', 'Style'))
        style.set('full', 'true')
    
    # 背景
    bg = ET.SubElement(style, 'Background')
    if config.get('background'):
        bg.set('name', 'ColorBackground')
        color_elem = ET.SubElement(bg, 'color')
        fine_color = ET.SubElement(color_elem, 'FineColor')
        fine_color.set('color', str(config['background']))
        # ⭐ 必须有 hor 和 ver 属性
        fine_color.set('hor', '-1')
        fine_color.set('ver', '-1')
    
    # 边框
    if config.get('border'):
        border = ET.SubElement(style, 'Border')
        for side in ['Top', 'Bottom', 'Left', 'Right']:
            side_elem = ET.SubElement(border, side)
            side_elem.set('style', '1')
            color = ET.SubElement(side_elem, 'color')
            fine_color = ET.SubElement(color, 'FineColor')
            fine_color.set('color', '-2432266')  # 边框颜色
            fine_color.set('hor', '-1')
            fine_color.set('ver', '-1')
```

### 2.6 _prettify() XML 格式化

**关键点：CDATA 格式转换**

```python
def _prettify(self, elem):
    # 格式化 XML
    dom = minidom.parseString(rough_string)
    pretty = dom.toprettyxml(indent='', encoding=None)
    
    # ⭐ 帆软兼容性：O 标签必须用 CDATA 格式
    # <O/> → <O>\n<![CDATA[]]></O>
    result = re.sub(r'<O\s*/>', '<O>\n<![CDATA[]]></O>', result)
    result = re.sub(r'<O></O>', '<O>\n<![CDATA[]]></O>', result)
    
    # 处理有值的 O 标签
    def replace_o_tag(match):
        content = match.group(1)
        if 'CDATA' in content:
            return match.group(0)
        return f'<O>\n<![CDATA[{content}]]></O>'
    
    result = re.sub(r'<O>([^<]*)</O>', replace_o_tag, result)
    return result
```

### 2.7 默认样式配置

```python
def _get_default_styles(self):
    """
    颜色说明（Java 有符号整数）:
    - RGB(233, 233, 255) = -1447425  表头背景色
    - RGB(218, 226, 246) = -2432266  边框颜色
    - RGB(0, 102, 204) = -8163329    金额字体颜色
    """
    return [
        # Style 0: 表头左列
        {
            "name": "表头左列",
            "horizontal_alignment": "2",  # 左对齐
            "font": {"name": "SimSun", "size": "80"},
            "background": "-1447425",     # ⭐ 表头背景色
            "border": True
        },
        # Style 1: 表头
        {
            "name": "表头",
            "horizontal_alignment": "2",
            "font": {"name": "宋体", "size": "80"},
            "background": "-1447425",
            "border": True
        },
        # Style 2: 数据
        {
            "name": "数据",
            "horizontal_alignment": "2",
            "border": True
        },
        # Style 3: 金额
        {
            "name": "金额",
            "horizontal_alignment": "4",  # 右对齐
            "font": {"color": "-8163329"},
            "format": "#,##0.00",
            "border": True
        }
    ]
```

---

## 三、web/app.py Web 服务

### 3.1 核心路由

```python
# 页面路由
@app.route('/excel-convert-v3')      # V3 界面

# API 路由
@app.route('/api/v2/generate')       # 报表生成 API ⭐ 核心
@app.route('/api/analyze/cpt')       # CPT 分析
@app.route('/api/download/<file>')   # 文件下载
```

### 3.2 generate_report_v2() 生成接口

**关键点：参数自动推断**

```python
@app.route('/api/v2/generate', methods=['POST'])
def generate_report_v2():
    data = request.json
    
    # 解析数据源
    datasource = data.get('datasource', {})
    
    if datasource.get('type') == 'class':
        param_template = datasource.get('parameter_template', [])
        params = []
        
        if param_template:
            # 使用用户配置的参数模板
            for item in param_template:
                for param_name, param_value in item.items():
                    params.append({'name': param_name, 'default': ...})
        else:
            # ⭐ 自动从 filter_components 推断参数
            for comp in filter_components:
                code = comp.get('code')
                if code:
                    params.append({'name': code, 'default': ''})
        
        cpt_config['data_sources'].append({
            'name': datasource.get('name'),
            'type': 'ClassTableData',
            'class_name': datasource.get('class_name'),
            'parameters': params
        })
    
    # 构建单元格配置
    for col_letter, mapping in column_mapping.items():
        # 表头
        cpt_config['cells'].append({
            'column': col_num,
            'row': 0,
            'value': header_name,
            'style_index': 1  # 表头样式
        })
        # 数据行
        cpt_config['cells'].append({
            'column': col_num,
            'row': 1,
            'value_type': 'DSColumn',
            'data_source': ds_name,
            'column_name': field_name,
            'expand_dir': 0,  # 纵向扩展
            'style_index': 3 if is_amount else 2
        })
    
    # 生成 CPT
    generator = CPTGenerator()
    cpt_content = generator.generate(cpt_config)
    
    return jsonify({
        'success': True,
        'download_url': f'/api/download/{filename}'
    })
```

---

## 四、前端 excel_convert_v3.html

### 4.1 数据收集 collectConfig()

```javascript
function collectConfig() {
    const config = {
        datasources: [],
        column_mapping: {},
        filter_components: [],
        styles: []
    };
    
    // 收集数据源（表单模式）
    document.querySelectorAll('.datasource-card').forEach(card => {
        const type = card.querySelector('.ds-type').value;
        const ds = {
            name: card.querySelector('.ds-name').value,
            type: type
        };
        
        if (type === 'class') {
            ds.class_name = card.querySelector('.ds-class-name').value;
            ds.return_fields = JSON.parse(card.querySelector('.ds-return-fields').value);
            ds.parameter_template = JSON.parse(card.querySelector('.ds-params').value);
        }
        
        config.datasources.push(ds);
    });
    
    // 收集列映射
    for (let i = 0; i < 18; i++) {
        const colLetter = String.fromCharCode(65 + i);
        const header = document.getElementById(`col_${i}_header`)?.value;
        const field = document.getElementById(`col_${i}_field`)?.value;
        
        if (field) {
            config.column_mapping[colLetter] = {
                header: header || field,
                field: field
            };
        }
    }
    
    // 收集筛选组件
    document.querySelectorAll('.filter-row-json').forEach(textarea => {
        const rowComponents = JSON.parse(textarea.value);
        rowComponents.forEach(comp => {
            if (comp.label && comp.code) {
                config.filter_components.push(comp);
            }
        });
    });
    
    return config;
}
```

### 4.2 样式配置

```javascript
// 颜色常量
const HEADER_BG = '-1447425';   // RGB(233,233,255)
const BORDER_COLOR = '-2432266'; // RGB(218,226,246)

// 默认样式
config.styles = [
    {"name": "表头左列", "background": "-1447425", "border": true},
    {"name": "表头", "background": "-1447425", "border": true},
    {"name": "数据", "border": true},
    {"name": "金额", "format": "#,##0.00", "border": true}
];
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
- [ ] 控件位置计算是否正确（89 + 4 + 135 + 10）？
- [ ] 参数名是否与筛选组件 code 一致？

---

_📅 文档更新日期: 2026-04-09_