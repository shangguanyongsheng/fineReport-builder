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
        """生成参数面板"""
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
        
        # 控件
        for i, ctrl in enumerate(controls):
            widget = self._generate_widget(ctrl, i)
            layout.append(widget)
        
        return param_attr
    
    def _generate_widget(self, ctrl: Dict, index: int) -> ET.Element:
        """生成控件"""
        widget = ET.Element('Widget')
        widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        
        inner = ET.SubElement(widget, 'InnerWidget')
        widget_type = ctrl.get('type', 'TextEditor')
        inner.set('class', f'com.fr.form.ui.{widget_type}')
        
        # 控件名称
        name = ET.SubElement(inner, 'WidgetName')
        name.set('name', ctrl.get('name', f'widget_{index}'))
        
        # 标签
        if ctrl.get('label'):
            label = ET.SubElement(inner, 'LabelName')
            label.set('name', ctrl['label'])
        
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
        if ctrl.get('default'):
            value = ET.SubElement(inner, 'widgetValue')
            o = ET.SubElement(value, 'O')
            o.text = ctrl['default']
        
        # 位置
        bounds = ET.SubElement(widget, 'BoundsAttr')
        bounds.set('x', str(ctrl.get('x', 100 + index * 150)))
        bounds.set('y', str(ctrl.get('y', 10)))
        bounds.set('width', str(ctrl.get('width', 135)))
        bounds.set('height', str(ctrl.get('height', 28)))
        
        return widget
    
    def _generate_style_list(self, styles: List[Dict]) -> ET.Element:
        """生成样式列表"""
        style_list = ET.Element('StyleList')
        
        # 默认样式
        default_style = ET.SubElement(style_list, 'Style')
        default_style.set('style_name', '默认')
        default_style.set('full', 'true')
        default_style.set('border_source', '-1')
        default_style.set('imageLayout', '1')
        
        font = ET.SubElement(default_style, 'FRFont')
        font.set('name', 'simhei')
        font.set('style', '0')
        font.set('size', '72')
        
        bg = ET.SubElement(default_style, 'Background')
        bg.set('name', 'NullBackground')
        
        border = ET.SubElement(default_style, 'Border')
        
        return style_list
    
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
        {"name": "startDate", "type": "DateEditor", "label": "开始日期", "x": 100, "y": 10},
        {"name": "endDate", "type": "DateEditor", "label": "结束日期", "x": 250, "y": 10},
        {"name": "region", "type": "ComboBox", "label": "区域", "options": {"east": "华东", "south": "华南", "north": "华北"}, "x": 400, "y": 10}
    ],
    "cells": [
        {"column": 0, "row": 0, "value": "区域", "style_index": 0},
        {"column": 1, "row": 0, "value": "产品", "style_index": 0},
        {"column": 2, "row": 0, "value": "金额", "style_index": 0},
        {"column": 3, "row": 0, "value": "数量", "style_index": 0},
        {"column": 0, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "region", "expand_dir": 0},
        {"column": 1, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "product"},
        {"column": 2, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "amount"},
        {"column": 3, "row": 1, "value_type": "DSColumn", "data_source": "sales_data", "column_name": "quantity"}
    ],
    "styles": []
}


if __name__ == "__main__":
    generator = CPTGenerator()
    cpt_content = generator.generate(SAMPLE_CONFIG)
    
    with open('sample_report.cpt', 'w', encoding='utf-8') as f:
        f.write(cpt_content)
    
    print("生成成功：sample_report.cpt")