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

            elif ds.get('type') == 'RecursionTableData':
                # 递归树数据源
                mf = ET.SubElement(table_data, 'markFields')
                mf.text = f"<![CDATA[{ds['mark_field_index']}]]>"

                pmf = ET.SubElement(table_data, 'parentmarkFields')
                pmf.text = f"<![CDATA[{ds['parent_mark_field_index']}]]>"

                mfn = ET.SubElement(table_data, 'markFieldsName')
                mfn.text = f"<![CDATA[{ds['mark_field_name']}]]>"

                pmfn = ET.SubElement(table_data, 'parentmarkFieldsName')
                pmfn.text = f"<![CDATA[{ds['parent_mark_field_name']}]]>"

                otn = ET.SubElement(table_data, 'originalTableDataName')
                otn.text = f"<![CDATA[{ds['base_data_source']}]]>"

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
            ctrl_type = ctrl.get('type', 'TextEditor')
            extra = {}
            if ctrl_type == 'TreeComboBoxEditor':
                extra['dict_data_source'] = ctrl.get('dict_data_source', '')
                extra['dict_ki'] = ctrl.get('dict_ki', 'dict_key')
                extra['dict_vi'] = ctrl.get('dict_vi', 'dict_value')
                extra['muti_select'] = ctrl.get('muti_select', 'false')
                extra['select_leaf_only'] = ctrl.get('select_leaf_only', 'false')
                extra['widget_id'] = ctrl.get('widget_id', '')

            input_widget = self._create_input_widget(
                name=code,
                ctrl_type=ctrl_type,
                x=x_input, y=y, w=INPUT_WIDTH, h=ROW_HEIGHT,
                **extra,
            )
            layout.append(input_widget)

        # 固定添加查询和重置按钮
        self._add_query_reset_buttons(layout, len(controls), controls)

    def _add_query_reset_buttons(self, layout: ET.Element, num_controls: int, controls: List[Dict[str, Any]]):
        """添加查询和重置按钮到筛选面板布局末尾

        Args:
            layout: 参数面板 Layout 节点
            num_controls: 筛选组件对数（不含按钮）
            controls: 筛选组件配置列表，用于生成重置按钮 JS
        """
        BUTTON_WIDTH = 89
        BUTTON_HEIGHT = 28
        START_X = 10
        START_Y = 10
        ROW_HEIGHT = 28
        ROW_GAP = 8

        # 计算按钮所在行：放在所有筛选组件行的下一行
        rows_filled = (num_controls + 4) // 5  # 每行 5 对
        y = START_Y + rows_filled * (ROW_HEIGHT + ROW_GAP)
        x_reset = START_X + 4 * (228 + 4) - 89  # 第 5 列位置
        x_query = START_X + 4 * (228 + 4)  # 第 5 列右侧

        # 生成重置按钮 JS：只重置空值参数，有默认值的不重置
        reset_js_lines = []
        for ctrl in controls:
            code = ctrl.get('code', '')
            if code and not ctrl.get('default'):  # 没有默认值才重置
                reset_js_lines.append(f'this.options.form.getWidgetByName("{code}").reset();')
        reset_content = '\n'.join(reset_js_lines) if reset_js_lines else 'null'

        # 重置按钮
        reset_btn = self._create_submit_button(
            name='Reload',
            text='重置',
            x=x_reset, y=y, w=BUTTON_WIDTH, h=BUTTON_HEIGHT,
            action='reset',
            js_content=reset_content,
        )
        layout.append(reset_btn)

        # 查询按钮
        query_btn = self._create_submit_button(
            name='Search',
            text='查询',
            x=x_query, y=y, w=BUTTON_WIDTH, h=BUTTON_HEIGHT,
            action='query',
        )
        layout.append(query_btn)

    def _create_submit_button(
        self, name: str, text: str, x: int, y: int, w: int, h: int,
        action: str = 'query',
        js_content: str = 'null',
    ) -> ET.Element:
        """创建 FormSubmitButton（查询/重置按钮）

        Args:
            name: 控件名称（Search / Reload）
            text: 按钮文本
            x, y, w, h: 位置和尺寸
            action: 'query' 或 'reset'
            js_content: 按钮点击 JS 内容
        """
        import uuid
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        inner = ET.SubElement(widget, 'InnerWidget')
        inner.set('class', 'com.fr.form.parameter.FormSubmitButton')

        # Listener
        listener = ET.SubElement(inner, 'Listener')
        if action == 'query':
            listener.set('event', 'click')
            listener.set('name', '点击1')
        else:
            listener.set('event', 'click')
            listener.set('name', '点击2')

        js = ET.SubElement(listener, 'JavaScript')
        js.set('class', 'com.fr.js.JavaScriptImpl')
        ET.SubElement(js, 'Parameters')
        content = ET.SubElement(js, 'Content')
        content.text = f'<![CDATA[{js_content}]]>'

        wname = ET.SubElement(inner, 'WidgetName')
        wname.set('name', name)

        if action == 'reset':
            label_name = ET.SubElement(inner, 'LabelName')
            label_name.set('name', '重置')

        wid = ET.SubElement(inner, 'WidgetID')
        wid.set('widgetID', str(uuid.uuid4()))

        wattr = ET.SubElement(inner, 'WidgetAttr')
        wattr.set('aspectRatioLocked', 'false')
        wattr.set('aspectRatioBackup', '-1.0')
        wattr.set('description', '')

        mb = ET.SubElement(wattr, 'MobileBookMark')
        mb.set('useBookMark', 'false')
        mb.set('bookMarkName', '')
        mb.set('frozen', 'false')
        mb.set('index', '-1')
        if action == 'query':
            mb.set('oldWidgetName', 'Search_c')
        else:
            mb.set('oldWidgetName', 'Reload_c')

        ET.SubElement(wattr, 'PrivilegeControl')

        text_elem = ET.SubElement(inner, 'Text')
        text_elem.text = f'<![CDATA[{text}]]>'

        hotkeys = ET.SubElement(inner, 'Hotkeys')
        hotkeys.text = '<![CDATA[enter]]>'

        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(x))
        bounds.set('y', str(y))
        bounds.set('width', str(w))
        bounds.set('height', str(h))

        return widget

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

    def _create_input_widget(self, name: str, ctrl_type: str, x: int, y: int, w: int, h: int, **kwargs) -> ET.Element:
        """创建输入控件 XML

        Args:
            name: 控件 code
            ctrl_type: 控件类型（TextEditor, ComboBox, TreeComboBoxEditor, DateEditor 等）
            x, y, w, h: 位置和尺寸
            **kwargs: 额外参数，TreeComboBoxEditor 需要：
                - dict_data_source: 绑定的树数据源名称
                - dict_ki: 字典 key 字段名（默认 dict_key）
                - dict_vi: 字典 value 字段名（默认 dict_value）
                - muti_select: 是否多选（默认 false）
                - select_leaf_only: 是否只选叶子（默认 false）
                - widget_id: 控件 UUID
        """
        import uuid
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        inner = ET.SubElement(widget, 'InnerWidget')
        inner.set('class', f"com.fr.form.ui.{ctrl_type}")
        wname = ET.SubElement(inner, 'WidgetName')
        wname.set('name', name)

        # TreeComboBoxEditor 需要 Dictionary 绑定
        if ctrl_type == 'TreeComboBoxEditor':
            wname_label = ET.SubElement(inner, 'LabelName')
            wname_label.set('name', name)

            wid = ET.SubElement(inner, 'WidgetID')
            wid.set('widgetID', kwargs.get('widget_id', str(uuid.uuid4())))

            wattr = ET.SubElement(inner, 'WidgetAttr')
            wattr.set('aspectRatioLocked', 'false')
            wattr.set('aspectRatioBackup', '-1.0')
            wattr.set('description', '')

            mb = ET.SubElement(wattr, 'MobileBookMark')
            mb.set('useBookMark', 'false')
            mb.set('bookMarkName', '')
            mb.set('frozen', 'false')
            mb.set('index', '-1')
            mb.set('oldWidgetName', '')

            ET.SubElement(wattr, 'PrivilegeControl')

            # TreeAttr
            tree_attr = ET.SubElement(inner, 'TreeAttr')
            tree_attr.set('mutiSelect', kwargs.get('muti_select', 'false'))
            tree_attr.set('selectLeafOnly', kwargs.get('select_leaf_only', 'false'))

            # Dictionary
            dictionary = ET.SubElement(inner, 'Dictionary')
            dictionary.set('class', 'com.fr.data.impl.TableDataDictionary')

            formula_dict = ET.SubElement(dictionary, 'FormulaDictAttr')
            formula_dict.set('kiName', kwargs.get('dict_ki', 'dict_key'))
            formula_dict.set('viName', kwargs.get('dict_vi', 'dict_value'))

            td_dict_attr = ET.SubElement(dictionary, 'TableDataDictAttr')
            td = ET.SubElement(td_dict_attr, 'TableData')
            td.set('class', 'com.fr.data.impl.NameTableData')
            td_name = ET.SubElement(td, 'Name')
            td_name.text = f"<![CDATA[{kwargs.get('dict_data_source', '')}]]>"

            ET.SubElement(inner, 'isLayerBuild').set('isLayerBuild', 'false')
            ET.SubElement(inner, 'isAutoBuild').set('autoBuild', 'true')
            ET.SubElement(inner, 'isPerformanceFirst').set('performanceFirst', 'false')
        else:
            # 普通控件只需要 widgetValue
            pass

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
