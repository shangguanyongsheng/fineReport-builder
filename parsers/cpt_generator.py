"""帆软 .cpt 文件生成器

根据结构化配置生成 .cpt 文件。
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class CPTGenerator:
    """CPT 文件生成器"""
    
    def __init__(self):
        self.template_version = "20211223"
        self.release_version = "11.5.0"
    
    def generate(self, config: Dict[str, Any]) -> str:
        """生成 .cpt 文件内容
        
        Args:
            config: 报表配置，包含：
                - title: 报表标题
                - data_sources: 数据源列表
                - filter_controls: 筛选控件列表
                - cells: 单元格列表
                - styles: 样式列表
        
        Returns:
            .cpt XML 内容
        """
        # 创建根节点
        root = ET.Element('WorkBook')
        root.set('xmlVersion', self.template_version)
        root.set('releaseVersion', self.release_version)
        
        # 1. 数据源映射
        table_data_map = self._generate_table_data_map(config.get('data_sources', []))
        root.append(table_data_map)
        
        # 2. Web 属性
        report_web_attr = self._generate_report_web_attr(config)
        root.append(report_web_attr)
        
        # 3. 报表主体
        report = self._generate_report(config)
        root.append(report)
        
        # 4. 参数面板
        report_parameter_attr = self._generate_parameter_attr(config.get('filter_controls', []))
        root.append(report_parameter_attr)
        
        # 5. 样式列表
        style_list = self._generate_style_list(config.get('styles', []))
        root.append(style_list)
        
        # 6. 其他属性
        self._append_meta_attributes(root)
        
        # 格式化输出
        return self._prettify(root)
    
    def _generate_table_data_map(self, data_sources: List[Dict]) -> ET.Element:
        """生成数据源映射"""
        table_data_map = ET.Element('TableDataMap')
        
        for ds in data_sources:
            table_data = ET.SubElement(table_data_map, 'TableData')
            table_data.set('name', ds.get('name', ''))
            table_data.set('class', f"com.fr.data.impl.{ds.get('type', 'DBTableData')}")
            
            # 脱敏设置
            desensitizations = ET.SubElement(table_data, 'Desensitizations')
            desensitizations.set('desensitizeOpen', 'false')
            
            # 参数
            if ds.get('parameters'):
                params_elem = ET.SubElement(table_data, 'Parameters')
                for param in ds['parameters']:
                    param_elem = ET.SubElement(params_elem, 'Parameter')
                    attr = ET.SubElement(param_elem, 'Attributes')
                    attr.set('name', param.get('name', ''))
                    default = ET.SubElement(param_elem, 'O')
                    default.text = param.get('default', '')
            
            # 连接
            if ds.get('database'):
                conn = ET.SubElement(table_data, 'Connection')
                conn.set('class', 'com.fr.data.impl.NameDatabaseConnection')
                db_name = ET.SubElement(conn, 'DatabaseName')
                db_name.text = ds['database']
            
            # SQL
            if ds.get('sql'):
                query = ET.SubElement(table_data, 'Query')
                query.text = ds['sql']
                page_query = ET.SubElement(table_data, 'PageQuery')
                page_query.text = ''
            
            # ClassTableData
            if ds.get('class_name'):
                class_attr = ET.SubElement(table_data, 'ClassTableDataAttr')
                class_attr.set('className', ds['class_name'])
        
        return table_data_map
    
    def _generate_report_web_attr(self, config: Dict) -> ET.Element:
        """生成 Web 属性"""
        web_attr = ET.Element('ReportWebAttr')
        
        # 标题
        title = ET.SubElement(web_attr, 'Title')
        title.text = config.get('title', '新建报表')
        
        # 工具栏等
        server_printer = ET.SubElement(web_attr, 'ServerPrinter')
        
        return web_attr
    
    def _generate_report(self, config: Dict) -> ET.Element:
        """生成报表主体"""
        report = ET.Element('Report')
        report.set('class', 'com.fr.report.worksheet.WorkSheet')
        report.set('name', config.get('sheet_name', 'Sheet1'))
        
        # 报表属性
        page_attr = ET.SubElement(report, 'ReportPageAttr')
        ET.SubElement(page_attr, 'HR')
        ET.SubElement(page_attr, 'FR')
        ET.SubElement(page_attr, 'HC')
        ET.SubElement(page_attr, 'FC')
        use_elem = ET.SubElement(page_attr, 'USE')
        use_elem.set('REPEAT', 'false')
        use_elem.set('PAGE', 'false')
        use_elem.set('WRITE', 'false')
        
        # 行高列宽
        row_height = ET.SubElement(report, 'RowHeight')
        row_height.set('defaultValue', '723900')
        
        col_width = ET.SubElement(report, 'ColumnWidth')
        col_width.set('defaultValue', '2743200')
        
        # 单元格列表
        cell_list = ET.SubElement(report, 'CellElementList')
        
        for cell in config.get('cells', []):
            cell_elem = self._generate_cell(cell)
            cell_list.append(cell_elem)
        
        # 报表属性设置
        attr_set = ET.SubElement(report, 'ReportAttrSet')
        report_settings = ET.SubElement(attr_set, 'ReportSettings')
        report_settings.set('headerHeight', '0')
        report_settings.set('footerHeight', '0')
        
        privilege = ET.SubElement(report, 'PrivilegeControl')
        
        return report
    
    def _generate_cell(self, cell: Dict) -> ET.Element:
        """生成单元格元素"""
        cell_elem = ET.Element('C')
        cell_elem.set('c', str(cell.get('column', 0)))
        cell_elem.set('r', str(cell.get('row', 0)))
        
        if cell.get('row_span', 1) > 1:
            cell_elem.set('rs', str(cell['row_span']))
        if cell.get('col_span', 1) > 1:
            cell_elem.set('cs', str(cell['col_span']))
        
        # 样式
        if cell.get('style_index'):
            cell_elem.set('s', str(cell['style_index']))
        
        # 值
        value = cell.get('value', '')
        value_type = cell.get('value_type', 'text')
        
        value_elem = ET.SubElement(cell_elem, 'O')
        
        if value_type == 'DSColumn':
            value_elem.set('t', 'DSColumn')
            attrs = ET.SubElement(value_elem, 'Attributes')
            attrs.set('dsName', cell.get('data_source', ''))
            attrs.set('columnName', cell.get('column_name', ''))
            
            # 扩展
            expand = ET.SubElement(cell_elem, 'Expand')
            if cell.get('expand_dir'):
                expand.set('dir', str(cell['expand_dir']))
        
        elif value_type == 'Formula':
            value_elem.set('t', 'XMLable')
            value_elem.set('class', 'com.fr.base.Formula')
            attrs = ET.SubElement(value_elem, 'Attributes')
            attrs.text = value
        
        else:
            value_elem.text = value
        
        # 权限控制
        privilege = ET.SubElement(cell_elem, 'PrivilegeControl')
        
        return cell_elem
    
    def _generate_parameter_attr(self, controls: List[Dict]) -> ET.Element:
        """生成参数面板
        
        布局规则：一行 5 对组件（Label + 输入控件）
        - Label 宽度: 70px
        - 输入控件宽度: 135px  
        - 每对间距: 10px
        - 行间距: 10px
        """
        param_attr = ET.Element('ReportParameterAttr')
        
        # 属性
        attrs = ET.SubElement(param_attr, 'Attributes')
        attrs.set('showWindow', 'true')
        attrs.set('delayPlaying', 'false')
        attrs.set('windowPosition', '1')
        attrs.set('align', '0')
        attrs.set('useParamsTemplate', 'true')
        attrs.set('currentIndex', '0')
        
        # 标题
        title = ET.SubElement(param_attr, 'PWTitle')
        title.text = '参数'
        
        # 参数 UI
        param_ui = ET.SubElement(param_attr, 'ParameterUI')
        param_ui.set('class', 'com.fr.form.main.parameter.FormParameterUI')
        
        # 布局
        layout = ET.SubElement(param_ui, 'Layout')
        layout.set('class', 'com.fr.form.ui.container.WParameterLayout')
        
        widget_name = ET.SubElement(layout, 'WidgetName')
        widget_name.set('name', 'para')
        
        # 布局参数
        LABEL_WIDTH = 70      # Label 控件宽度
        INPUT_WIDTH = 135     # 输入控件宽度
        GAP = 10              # 控件间距
        ROW_HEIGHT = 28       # 控件高度
        PAIRS_PER_ROW = 5     # 每行组件对数
        START_X = 10          # 起始 X 坐标
        START_Y = 10          # 起始 Y 坐标
        
        # 生成控件（每对：Label + 输入控件）
        widget_index = 0
        for i, ctrl in enumerate(controls):
            # 计算位置
            row = i // PAIRS_PER_ROW
            col = i % PAIRS_PER_ROW
            
            # 每对的总宽度 = Label + GAP + Input
            pair_width = LABEL_WIDTH + GAP + INPUT_WIDTH
            pair_start_x = START_X + col * (pair_width + GAP * 2)
            pair_start_y = START_Y + row * (ROW_HEIGHT + GAP)
            
            # 1. 生成 Label 控件
            label_text = ctrl.get('label', ctrl.get('name', f'控件{i+1}'))
            label_widget = self._generate_label_widget(
                text=label_text,
                x=pair_start_x,
                y=pair_start_y,
                width=LABEL_WIDTH,
                height=ROW_HEIGHT,
                index=widget_index
            )
            layout.append(label_widget)
            widget_index += 1
            
            # 2. 生成输入控件
            input_widget = self._generate_widget(
                ctrl, 
                x=pair_start_x + LABEL_WIDTH + GAP,
                y=pair_start_y,
                width=INPUT_WIDTH,
                height=ROW_HEIGHT,
                index=widget_index
            )
            layout.append(input_widget)
            widget_index += 1
        
        return param_attr
    
    def _generate_label_widget(self, text: str, x: int, y: int, width: int, height: int, index: int) -> ET.Element:
        """生成 Label 标签控件"""
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        
        inner = ET.SubElement(widget, 'InnerWidget')
        inner.set('class', 'com.fr.form.ui.Label')
        
        # 控件名称
        name = ET.SubElement(inner, 'WidgetName')
        name.set('name', f'label_{index}')
        
        # 标签文本
        widget_value = ET.SubElement(inner, 'widgetValue')
        o = ET.SubElement(widget_value, 'O')
        o.text = text
        
        # 位置
        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(x))
        bounds.set('y', str(y))
        bounds.set('width', str(width))
        bounds.set('height', str(height))
        
        return widget
    
    def _generate_widget(self, ctrl: Dict, x: int = None, y: int = None, width: int = 135, height: int = 28, index: int = 0) -> ET.Element:
        """生成输入控件
        
        Args:
            ctrl: 控件配置
            x: X 坐标
            y: Y 坐标  
            width: 控件宽度
            height: 控件高度
            index: 控件索引
        """
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        
        inner = ET.SubElement(widget, 'InnerWidget')
        widget_type = ctrl.get('type', 'TextEditor')
        inner.set('class', f'com.fr.form.ui.{widget_type}')
        
        # 控件名称（用 code 作为控件名，用于参数绑定）
        ctrl_name = ctrl.get('code', ctrl.get('name', f'widget_{index}'))
        name = ET.SubElement(inner, 'WidgetName')
        name.set('name', ctrl_name)
        
        # 下拉选项
        if ctrl.get('options'):
            dict_elem = ET.SubElement(inner, 'Dictionary')
            dict_elem.set('class', 'com.fr.data.impl.CustomDictionary')
            dict_attr = ET.SubElement(dict_elem, 'CustomDictAttr')
            for key, value in ctrl['options'].items():
                dict_item = ET.SubElement(dict_attr, 'Dict')
                dict_item.set('key', key)
                dict_item.set('value', value)
        
        # 默认值
        default_val = ctrl.get('default') or ctrl.get('default_value')
        if default_val:
            value = ET.SubElement(inner, 'widgetValue')
            o = ET.SubElement(value, 'O')
            o.text = default_val
        
        # 位置
        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(x if x is not None else ctrl.get('x', 100 + index * 150)))
        bounds.set('y', str(y if y is not None else ctrl.get('y', 10)))
        bounds.set('width', str(width))
        bounds.set('height', str(height))
        
        return widget
    
    def _generate_style_list(self, styles: List[Dict]) -> ET.Element:
        """生成样式列表
        
        支持自定义样式配置，格式：
        [
            {
                "name": "表头样式",
                "horizontal_alignment": "2",  # 2=左, 0=中, 4=右
                "font": {"name": "SimSun", "size": "80", "style": "0"},
                "background": "-1447425",  # 颜色值，None 表示透明
                "border": True
            }
        ]
        """
        style_list = ET.Element('StyleList')
        
        # 如果没有配置样式，使用默认样式集
        if not styles:
            styles = self._get_default_styles()
        
        for style_config in styles:
            style_elem = self._create_style_element(style_config)
            style_list.append(style_elem)
        
        return style_list
    
    def _get_default_styles(self) -> List[Dict]:
        """获取默认样式集（参考 FinanceCreditContractAnalysis.cpt）"""
        return [
            # Style 0: 表头左列样式（蓝色背景，左对齐）
            {
                "name": "表头左列",
                "horizontal_alignment": "2",
                "font": {"name": "SimSun", "style": "0", "size": "80"},
                "background": "-1447425",  # 淡蓝色背景
                "border": True
            },
            # Style 1: 表头样式（蓝色背景，左对齐）
            {
                "name": "表头",
                "horizontal_alignment": "2",
                "font": {"name": "宋体", "style": "0", "size": "80"},
                "background": "-1447425",
                "border": True
            },
            # Style 2: 数据样式（无背景，左对齐，有边框）
            {
                "name": "数据",
                "horizontal_alignment": "2",
                "font": {"name": "SimSun", "style": "0", "size": "80"},
                "background": None,
                "border": True
            },
            # Style 3: 金额样式（右对齐，数字格式，蓝色字体）
            {
                "name": "金额",
                "horizontal_alignment": "4",
                "font": {"name": "SimSun", "style": "0", "size": "80", "color": "-8163329"},
                "background": "-1",  # 白色背景
                "border": True,
                "format": "#,##0.00"
            },
            # Style 4: 默认样式
            {
                "name": "默认",
                "horizontal_alignment": "0",
                "font": {"name": "simhei", "style": "0", "size": "72"},
                "background": None,
                "border": False,
                "is_default": True
            }
        ]
    
    def _create_style_element(self, config: Dict) -> ET.Element:
        """创建单个样式元素"""
        style = ET.Element('Style')
        
        # 样式名称
        style.set('style_name', str(config.get('name', 'Style')))
        
        # 默认样式标记
        if config.get('is_default'):
            style.set('full', 'true')
            style.set('border_source', '-1')
        
        # 对齐方式 - 确保转换为字符串
        if config.get('horizontal_alignment') is not None:
            style.set('horizontal_alignment', str(config['horizontal_alignment']))
        
        style.set('imageLayout', '1')
        
        # 数字格式
        if config.get('format'):
            fmt = ET.SubElement(style, 'Format')
            fmt.set('class', 'com.fr.base.CoreDecimalFormat')
            fmt.set('roundingMode', '6')
            fmt.text = str(config['format'])
        
        # 字体
        font_config = config.get('font', {})
        font = ET.SubElement(style, 'FRFont')
        font.set('name', str(font_config.get('name', 'SimSun')))
        font.set('style', str(font_config.get('style', '0')))
        font.set('size', str(font_config.get('size', '80')))
        
        # 字体颜色
        if font_config.get('color'):
            fg = ET.SubElement(font, 'foreground')
            color = ET.SubElement(fg, 'FineColor')
            color.set('color', str(font_config['color']))
        
        # 背景
        bg = ET.SubElement(style, 'Background')
        bg_color = config.get('background')
        if bg_color:
            bg.set('name', 'ColorBackground')
            color_elem = ET.SubElement(bg, 'color')
            fine_color = ET.SubElement(color_elem, 'FineColor')
            fine_color.set('color', str(bg_color))
        else:
            bg.set('name', 'NullBackground')
        
        # 边框
        if config.get('border'):
            border = ET.SubElement(style, 'Border')
            for side in ['Top', 'Bottom', 'Left', 'Right']:
                side_elem = ET.SubElement(border, side)
                side_elem.set('style', '1')
                color = ET.SubElement(side_elem, 'FineColor')
                color.set('color', '-2432266')  # 灰色边框
        elif config.get('is_default'):
            ET.SubElement(style, 'Border')
        
        return style
    
    def _append_meta_attributes(self, root: ET.Element):
        """添加元数据属性"""
        # 脱敏列表
        desensitization = ET.SubElement(root, 'DesensitizationList')
        
        # 设计器版本
        designer = ET.SubElement(root, 'DesignerVersion')
        designer.set('DesignerVersion', 'LAA')
        
        # 预览类型
        preview = ET.SubElement(root, 'PreviewType')
        preview.set('PreviewType', '2')
        
        # 模板 ID
        template_id = str(uuid.uuid4())
        fork_id = ET.SubElement(root, 'ForkIdAttrMark')
        fork_id.set('class', 'com.fr.base.iofile.attr.ForkIdAttrMark')
        fork_id_elem = ET.SubElement(fork_id, 'ForkIdAttrMark')
        fork_id_elem.set('forkId', template_id)
    
    def _prettify(self, elem: ET.Element) -> str:
        """格式化 XML 输出"""
        rough_string = ET.tostring(elem, encoding='unicode')
        
        # 使用 minidom 格式化
        dom = minidom.parseString(rough_string)
        pretty = dom.toprettyxml(indent='', encoding=None)
        
        # 移除空行
        lines = [line for line in pretty.split('\n') if line.strip()]
        
        # 添加 XML 声明
        if not lines[0].startswith('<?xml'):
            lines.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
        
        return '\n'.join(lines)


# 示例配置
SAMPLE_CONFIG = {
    "title": "销售统计报表",
    "sheet_name": "销售分析",
    "data_sources": [
        {
            "name": "sales_data",
            "type": "DBTableData",
            "database": "sales_db",
            "sql": "SELECT region, product, amount, quantity FROM sales WHERE date >= '${startDate}' AND date <= '${endDate}'",
            "parameters": [
                {"name": "startDate", "default": ""},
                {"name": "endDate", "default": ""},
                {"name": "region", "default": ""}
            ]
        }
    ],
    "filter_controls": [
        {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
        {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
        {"label": "区域", "code": "region", "type": "ComboBox", "options": {"east": "华东", "south": "华南", "north": "华北"}}
    ],
    "cells": [
        # 表头行 (使用 style_index 0 或 1)
        {"column": 0, "row": 0, "value": "区域", "style_index": 0},
        {"column": 1, "row": 0, "value": "产品", "style_index": 1},
        {"column": 2, "row": 0, "value": "金额", "style_index": 1},
        {"column": 3, "row": 0, "value": "数量", "style_index": 1},
        # 数据行 (使用 style_index 2 或 3)
        {"column": 0, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "region", "expand_dir": 0, "style_index": 2},
        {"column": 1, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "product", "style_index": 2},
        {"column": 2, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "amount", "style_index": 3},
        {"column": 3, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "quantity", "style_index": 2}
    ],
    "styles": []  # 空数组表示使用默认样式集
}


if __name__ == "__main__":
    generator = CPTGenerator()
    cpt_content = generator.generate(SAMPLE_CONFIG)
    
    with open('sample_report.cpt', 'w', encoding='utf-8') as f:
        f.write(cpt_content)
    
    print("生成成功：sample_report.cpt")