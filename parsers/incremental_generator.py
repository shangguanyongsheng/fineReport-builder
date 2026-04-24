"""增量式 CPT 生成器 — 基于模板修改关键区域

工作流程：
1. 复制模板（detail 或 manager）
2. 替换 TableDataMap（数据源）
3. 替换 CellElementList（单元格）
4. 替换 ReportParameterAttr/Layout（筛选组件）
5. 保留其余所有节点（ReportWebAttr、DesignerVersion、ForkIdAttrMark 等）
"""
import copy
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from parsers.sql_data_source import SqlDataSourceGenerator

# 模板路径
TEMPLATE_DIR = Path(__file__).parent.parent / 'templates'
TEMPLATES = {
    'detail': TEMPLATE_DIR / 'detail' / 'FinancingInternalLending.cpt',
    'manager': TEMPLATE_DIR / 'manager' / 'FinancingInternalLendingAnalysis.cpt',
}


class IncrementalCPTGenerator:
    """基于模板的增量 CPT 生成器"""

    def __init__(self, template_type: str = 'detail'):
        """
        Args:
            template_type: 'detail' 或 'manager'
        """
        if template_type not in TEMPLATES:
            raise ValueError(f"未知模板类型: {template_type}，可选: {list(TEMPLATES.keys())}")
        self.template_path = TEMPLATES[template_type]
        self.tree = None
        self.root = None

    def load_template(self):
        """加载模板"""
        self.tree = ET.parse(str(self.template_path))
        self.root = self.tree.getroot()

    def _resolve_data_source(self, ds: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据源配置，支持 sql_template 引用

        如果配置中包含 sql_template，则从模板文件加载 SQL 并合并参数。
        """
        if not ds.get("sql_template"):
            return ds

        sql_gen = SqlDataSourceGenerator()
        template_path = ds["sql_template"]
        database = ds.get("database", "cfs-report")

        # 模板变量：从配置中提取
        variables = ds.get("template_variables", {})
        # 租户参数默认从 fine_username9 映射
        tenant_param = ds.get("tenant_param", "fine_username9")
        if "tenant_param" not in variables:
            variables["tenant_param"] = tenant_param

        template_ds = sql_gen.from_template_file(
            name=ds["name"],
            template_path=template_path,
            database=database,
            variables=variables,
            parameters=ds.get("parameters", []),
        )

        # 合并其他字段
        for key, value in ds.items():
            if key not in ("sql_template", "template_variables", "tenant_param") and key not in template_ds:
                template_ds[key] = value

        return template_ds

    def replace_data_sources(self, data_sources: List[Dict[str, Any]]):
        """替换 TableDataMap 中的数据源

        清空原有 TableDataMap，写入新的数据源定义。
        支持 sql_template 字段，自动从 base_sql_templates 加载。
        """
        tdm = self.root.find('TableDataMap')
        if tdm is None:
            tdm = ET.SubElement(self.root, 'TableDataMap')
        # 清空
        for child in list(tdm):
            tdm.remove(child)

        for ds in data_sources:
            # 解析模板引用
            ds = self._resolve_data_source(ds)

            table_data = ET.SubElement(tdm, 'TableData')
            table_data.set('name', ds.get('name', ''))
            ds_type = ds.get('type', 'DBTableData')
            table_data.set('class', f"com.fr.data.impl.{ds_type}")

            # 脱敏
            desens = ET.SubElement(table_data, 'Desensitizations')
            desens.set('desensitizeOpen', 'false')

            # 参数
            if ds.get('type') == 'ClassTableData':
                params_elem = ET.SubElement(table_data, 'Parameters')
                for p in ds.get('parameters', []):
                    param = ET.SubElement(params_elem, 'Parameter')
                    attrs = ET.SubElement(param, 'Attributes')
                    attrs.set('name', p.get('name', ''))
                    o = ET.SubElement(param, 'O')
                    o.text = f"<![CDATA[{p.get('default', '')}]]>"

                # Class 路径
                cls = ET.SubElement(table_data, 'ClassTableDataAttr')
                cls.set('className', ds.get('class_name', ''))

            elif ds.get('type') == 'DBTableData':
                params_elem = ET.SubElement(table_data, 'Parameters')
                for p in ds.get('parameters', []):
                    param = ET.SubElement(params_elem, 'Parameter')
                    attrs = ET.SubElement(param, 'Attributes')
                    attrs.set('name', p.get('name', ''))
                    o = ET.SubElement(param, 'O')
                    o.text = f"<![CDATA[{p.get('default', '')}]]>"

                # Attributes
                attr = ET.SubElement(table_data, 'Attributes')
                attr.set('maxMemRowCount', '-1')

                # Connection
                conn = ET.SubElement(table_data, 'Connection')
                conn.set('class', 'com.fr.data.impl.NameDatabaseConnection')
                dbname = ET.SubElement(conn, 'DatabaseName')
                dbname.text = f"<![CDATA[{ds.get('database', '')}]]>"

                # Query
                query = ET.SubElement(table_data, 'Query')
                query.text = f"<![CDATA[{ds.get('sql', '')}]]>"

                # PageQuery
                pq = ET.SubElement(table_data, 'PageQuery')
                pq.text = '<![CDATA[]]>'

    def replace_cells(self, cells: List[Dict[str, Any]]):
        """替换 CellElementList 中的单元格

        清空原有 CellElementList，写入新的单元格。
        """
        cel = self.root.find('.//CellElementList')
        if cel is None:
            report = self.root.find('.//Report')
            if report is not None:
                cel = ET.SubElement(report, 'CellElementList')
            else:
                return

        # 清空
        for child in list(cel):
            cel.remove(child)

        for cell in cells:
            c_elem = ET.SubElement(cel, 'C')
            c_elem.set('c', str(cell.get('column', 0)))
            c_elem.set('r', str(cell.get('row', 0)))
            if 'style_index' in cell:
                c_elem.set('s', str(cell['style_index']))

            value_type = cell.get('value_type', 'Static')
            if value_type == 'DSColumn':
                o = ET.SubElement(c_elem, 'O')
                o.set('t', 'DSColumn')
                attrs = ET.SubElement(o, 'Attributes')
                attrs.set('dsName', cell.get('data_source', ''))
                attrs.set('columnName', cell.get('column_name', ''))
            elif value_type == 'Formula':
                o = ET.SubElement(c_elem, 'O')
                o.set('t', 'XMLable')
                o.set('class', 'com.fr.base.Formula')
                o.text = cell.get('value', '')
            else:
                o = ET.SubElement(c_elem, 'O')
                o.text = f"<![CDATA[{cell.get('value', '')}]]>"

            priv = ET.SubElement(c_elem, 'PrivilegeControl')
            expand = ET.SubElement(c_elem, 'Expand')
            if 'expand_dir' in cell:
                expand.set('dir', str(cell['expand_dir']))
            ET.SubElement(expand, 'cellSortAttr')

    def replace_filter_controls(self, controls: List[Dict[str, Any]]):
        """替换 ReportParameterAttr > ParameterUI > Layout 中的筛选组件

        清空原有 Layout 中的 Widget，写入新的 Label + 输入控件对。
        """
        rpa = self.root.find('ReportParameterAttr')
        if rpa is None:
            return
        param_ui = rpa.find('ParameterUI')
        if param_ui is None:
            return
        layout = param_ui.find('Layout')
        if layout is None:
            return

        # 清空 Widget
        for widget in list(layout.findall('Widget')):
            layout.remove(widget)

        # 布局常量
        LABEL_WIDTH = 89
        INPUT_WIDTH = 135
        LABEL_INPUT_GAP = 4
        ROW_HEIGHT = 28
        ROW_GAP = 8
        PAIRS_PER_ROW = 5
        START_X = 10
        START_Y = 10
        pair_width = LABEL_WIDTH + LABEL_INPUT_GAP + INPUT_WIDTH
        PAIR_GAP = 4

        for i, ctrl in enumerate(controls):
            row = i // PAIRS_PER_ROW
            col = i % PAIRS_PER_ROW
            x_label = START_X + col * (pair_width + PAIR_GAP)
            x_input = x_label + LABEL_WIDTH + LABEL_INPUT_GAP
            y = START_Y + row * (ROW_HEIGHT + ROW_GAP)
            code = ctrl.get('code', f'param_{i}')

            # Label
            label_widget = self._create_label_widget(
                name=f'label_{code}',
                text=ctrl.get('label', code),
                x=x_label, y=y, w=LABEL_WIDTH, h=ROW_HEIGHT
            )
            layout.append(label_widget)

            # Input
            input_widget = self._create_input_widget(
                name=code,
                ctrl_type=ctrl.get('type', 'TextEditor'),
                x=x_input, y=y, w=INPUT_WIDTH, h=ROW_HEIGHT
            )
            layout.append(input_widget)

    def _create_label_widget(self, name: str, text: str, x: int, y: int, w: int, h: int) -> ET.Element:
        """创建 Label 控件 XML"""
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        inner = ET.SubElement(widget, 'InnerWidget')
        inner.set('class', 'com.fr.form.ui.Label')
        wname = ET.SubElement(inner, 'WidgetName')
        wname.set('name', name)
        wv = ET.SubElement(inner, 'widgetValue')
        o = ET.SubElement(wv, 'O')
        o.text = text
        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(x))
        bounds.set('y', str(y))
        bounds.set('width', str(w))
        bounds.set('height', str(h))
        return widget

    def _create_input_widget(self, name: str, ctrl_type: str, x: int, y: int, w: int, h: int) -> ET.Element:
        """创建输入控件 XML"""
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        inner = ET.SubElement(widget, 'InnerWidget')
        inner.set('class', f"com.fr.form.ui.{ctrl_type}")
        wname = ET.SubElement(inner, 'WidgetName')
        wname.set('name', name)
        wv = ET.SubElement(inner, 'widgetValue')
        o = ET.SubElement(wv, 'O')
        o.text = '<![CDATA[]]>'
        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(x))
        bounds.set('y', str(y))
        bounds.set('width', str(w))
        bounds.set('height', str(h))
        return widget

    def generate(self, config: Dict[str, Any], output_path: str = '') -> str:
        """生成 CPT 文件

        Args:
            config: 包含 data_sources, cells, filter_controls
            output_path: 输出路径，默认自动生成

        Returns:
            输出文件路径
        """
        self.load_template()

        if 'data_sources' in config:
            self.replace_data_sources(config['data_sources'])

        if 'cells' in config:
            self.replace_cells(config['cells'])

        if 'filter_controls' in config:
            self.replace_filter_controls(config['filter_controls'])

        if not output_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            title = config.get('title', 'report').replace('/', '_')
            output_path = f"outputs/{title}_{ts}.cpt"

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # 写回 XML
        raw = ET.tostring(self.root, encoding='unicode')
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw
        with open(out, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        return str(out)
