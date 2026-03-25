"""帆软 .cpt 文件解析器

解析 .cpt 文件结构，提取数据源、筛选区域、数据展示区三大核心模块。
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class TableDataParameter:
    """数据集参数"""
    name: str
    default_value: str = ""


@dataclass
class TableData:
    """数据集定义"""
    name: str
    class_type: str  # DBTableData, ClassTableData, RecursionTableData
    database: str = ""
    sql: str = ""
    parameters: List[TableDataParameter] = field(default_factory=list)
    class_name: str = ""  # ClassTableData 的类名


@dataclass
class WidgetControl:
    """控件定义"""
    name: str
    widget_type: str  # TextEditor, DateEditor, ComboBox, TreeComboBoxEditor 等
    label: str = ""
    dictionary: Dict[str, str] = field(default_factory=dict)  # 下拉选项
    default_value: str = ""
    bounds: Dict[str, int] = field(default_factory=dict)  # x, y, width, height


@dataclass
class CellElement:
    """单元格元素"""
    column: int
    row: int
    row_span: int = 1
    col_span: int = 1
    value: str = ""
    value_type: str = "text"  # text, DSColumn, Formula
    data_source: str = ""
    column_name: str = ""
    expand_dir: str = ""  # 0=纵向扩展, 1=横向扩展
    style_index: int = 0


@dataclass
class CPTStructure:
    """CPT 文件结构"""
    title: str = ""
    table_data_list: List[TableData] = field(default_factory=list)
    widget_controls: List[WidgetControl] = field(default_factory=list)
    cell_elements: List[CellElement] = field(default_factory=list)
    styles: List[Dict] = field(default_factory=list)
    javascript_listeners: List[Dict] = field(default_factory=list)


class CPTParser:
    """CPT 文件解析器"""
    
    def __init__(self):
        self.ns = {}  # XML 命名空间（如果需要）
    
    def parse(self, file_path: str) -> CPTStructure:
        """解析 .cpt 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理 CDATA 和特殊字符
        content = self._clean_xml(content)
        
        root = ET.fromstring(content)
        structure = CPTStructure()
        
        # 解析标题
        structure.title = self._parse_title(root)
        
        # 解析数据源
        structure.table_data_list = self._parse_table_data_map(root)
        
        # 解析筛选区域（参数面板）
        structure.widget_controls = self._parse_parameter_ui(root)
        
        # 解析数据展示区（单元格）
        structure.cell_elements = self._parse_cell_elements(root)
        
        # 解析样式
        structure.styles = self._parse_styles(root)
        
        # 解析 JavaScript 监听器
        structure.javascript_listeners = self._parse_listeners(root)
        
        return structure
    
    def _clean_xml(self, content: str) -> str:
        """清理 XML 内容"""
        # 移除可能的 BOM
        if content.startswith('\ufeff'):
            content = content[1:]
        return content
    
    def _parse_title(self, root: ET.Element) -> str:
        """解析报表标题"""
        title_elem = root.find('.//ReportWebAttr/Title')
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return ""
    
    def _parse_table_data_map(self, root: ET.Element) -> List[TableData]:
        """解析数据源映射"""
        table_data_list = []
        table_data_map = root.find('TableDataMap')
        
        if table_data_map is None:
            return table_data_list
        
        for table_data_elem in table_data_map.findall('TableData'):
            table_data = TableData(
                name=table_data_elem.get('name', ''),
                class_type=table_data_elem.get('class', '').split('.')[-1]
            )
            
            # 解析参数
            params_elem = table_data_elem.find('Parameters')
            if params_elem is not None:
                for param_elem in params_elem.findall('Parameter'):
                    name_elem = param_elem.find('Attributes')
                    if name_elem is not None:
                        param = TableDataParameter(
                            name=name_elem.get('name', '')
                        )
                        # 默认值
                        default_elem = param_elem.find('O')
                        if default_elem is not None and default_elem.text:
                            param.default_value = default_elem.text.strip()
                        table_data.parameters.append(param)
            
            # 解析数据库连接
            conn_elem = table_data_elem.find('Connection')
            if conn_elem is not None:
                db_elem = conn_elem.find('DatabaseName')
                if db_elem is not None and db_elem.text:
                    table_data.database = db_elem.text.strip()
            
            # 解析 SQL
            query_elem = table_data_elem.find('Query')
            if query_elem is not None and query_elem.text:
                table_data.sql = query_elem.text.strip()
            
            # 解析 ClassTableData 的类名
            class_elem = table_data_elem.find('ClassTableDataAttr')
            if class_elem is not None:
                table_data.class_name = class_elem.get('className', '')
            
            table_data_list.append(table_data)
        
        return table_data_list
    
    def _parse_parameter_ui(self, root: ET.Element) -> List[WidgetControl]:
        """解析参数面板控件"""
        controls = []
        
        # 查找参数面板
        param_ui = root.find('.//ReportParameterAttr/ParameterUI/Layout')
        if param_ui is None:
            return controls
        
        for widget_elem in param_ui.findall('Widget'):
            inner_widget = widget_elem.find('InnerWidget')
            if inner_widget is None:
                continue
            
            control = WidgetControl(
                name=inner_widget.get('name', ''),
                widget_type=inner_widget.tag
            )
            
            # 解析 Label
            label_elem = inner_widget.find('LabelName')
            if label_elem is not None and label_elem.text:
                control.label = label_elem.text.strip()
            
            # 解析下拉选项
            dict_elem = inner_widget.find('Dictionary')
            if dict_elem is not None:
                for dict_attr in dict_elem.findall('.//Dict'):
                    key = dict_attr.get('key', '')
                    value = dict_attr.get('value', '')
                    if key:
                        control.dictionary[key] = value
            
            # 解析默认值
            value_elem = inner_widget.find('widgetValue/O')
            if value_elem is not None and value_elem.text:
                control.default_value = value_elem.text.strip()
            
            # 解析位置
            bounds_elem = widget_elem.find('BoundsAttr')
            if bounds_elem is not None:
                control.bounds = {
                    'x': int(bounds_elem.get('x', 0)),
                    'y': int(bounds_elem.get('y', 0)),
                    'width': int(bounds_elem.get('width', 100)),
                    'height': int(bounds_elem.get('height', 28))
                }
            
            controls.append(control)
        
        return controls
    
    def _parse_cell_elements(self, root: ET.Element) -> List[CellElement]:
        """解析单元格元素"""
        cells = []
        
        # 查找单元格列表
        cell_list = root.find('.//Report/CellElementList')
        if cell_list is None:
            return cells
        
        for cell_elem in cell_list.findall('C'):
            cell = CellElement(
                column=int(cell_elem.get('c', 0)),
                row=int(cell_elem.get('r', 0)),
                row_span=int(cell_elem.get('rs', 1)),
                col_span=int(cell_elem.get('cs', 1))
            )
            
            # 解析单元格值
            value_elem = cell_elem.find('O')
            if value_elem is not None:
                cell.value_type = value_elem.get('t', 'text')
                
                if cell.value_type == 'DSColumn':
                    # 数据绑定
                    attrs = value_elem.find('Attributes')
                    if attrs is not None:
                        cell.data_source = attrs.get('dsName', '')
                        cell.column_name = attrs.get('columnName', '')
                elif cell.value_type == 'XMLable':
                    # 公式
                    formula_elem = value_elem.find('Attributes')
                    if formula_elem is not None and formula_elem.text:
                        cell.value = formula_elem.text.strip()
                        cell.value_type = 'Formula'
                else:
                    # 文本
                    if value_elem.text:
                        cell.value = value_elem.text.strip()
            
            # 解析扩展方向
            expand_elem = cell_elem.find('Expand')
            if expand_elem is not None:
                cell.expand_dir = expand_elem.get('dir', '')
            
            # 解析样式
            style_elem = cell_elem.find('s')
            if style_elem is not None:
                cell.style_index = int(style_elem.text) if style_elem.text else 0
            
            cells.append(cell)
        
        return cells
    
    def _parse_styles(self, root: ET.Element) -> List[Dict]:
        """解析样式列表"""
        styles = []
        style_list = root.find('StyleList')
        
        if style_list is None:
            return styles
        
        for style_elem in style_list.findall('Style'):
            style = {}
            style['font'] = style_elem.findtext('FRFont', '')
            style['background'] = style_elem.findtext('Background', '')
            styles.append(style)
        
        return styles
    
    def _parse_listeners(self, root: ET.Element) -> List[Dict]:
        """解析 JavaScript 监听器"""
        listeners = []
        
        for listener_elem in root.findall('.//Listener'):
            listener = {
                'event': listener_elem.get('event', ''),
                'script': ''
            }
            content_elem = listener_elem.find('.//Content')
            if content_elem is not None and content_elem.text:
                listener['script'] = content_elem.text.strip()
            listeners.append(listener)
        
        return listeners
    
    def to_summary(self, structure: CPTStructure) -> Dict[str, Any]:
        """转换为可读摘要"""
        return {
            "title": structure.title,
            "data_sources": [
                {
                    "name": td.name,
                    "type": td.class_type,
                    "database": td.database,
                    "sql_preview": td.sql[:100] + "..." if len(td.sql) > 100 else td.sql,
                    "parameters": [p.name for p in td.parameters]
                }
                for td in structure.table_data_list
            ],
            "filter_controls": [
                {
                    "name": c.name,
                    "type": c.widget_type,
                    "label": c.label,
                    "options_count": len(c.dictionary)
                }
                for c in structure.widget_controls
            ],
            "cells_count": len(structure.cell_elements),
            "styles_count": len(structure.styles)
        }


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cpt_parser.py <file.cpt>")
        sys.exit(1)
    
    parser = CPTParser()
    structure = parser.parse(sys.argv[1])
    summary = parser.to_summary(structure)
    
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))