#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FineReport Builder Agent v2.0 - 核心模块
基于模板的报表生成 Agent，支持：
- 复制 XML 节点方式增删筛选组件
- key-value 数据源参数配置
- 动态增删数据列单元格
- 参数校验（数据源参数只能多不能少）
"""

import os
import json
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET


class MemoryManager:
    """记忆管理器 - 双记忆系统"""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.templates_dir = self.memory_dir / "templates"
        self.memory_file = self.memory_dir / "AGENT_MEMORY.md"
        self.corrections_file = self.memory_dir / "corrections.jsonl"
        self.success_file = self.memory_dir / "success_patterns.jsonl"
    
    def load_template_knowledge(self, template_type: str) -> Dict:
        """加载模板知识"""
        template_file = self.templates_dir / f"{template_type}.json"
        if template_file.exists():
            return json.loads(template_file.read_text(encoding='utf-8'))
        return {}
    
    def record_correction(self, error_type: str, error_msg: str, fix: str, context: Dict = None):
        """记录纠正"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error": error_msg,
            "fix": fix,
            "context": context
        }
        with open(self.corrections_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
    
    def record_success(self, pattern_type: str, pattern: Dict):
        """记录成功模式"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": pattern_type,
            **pattern
        }
        with open(self.success_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record


class ReActEngine:
    """ReAct 引擎"""
    
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.trajectory = []
        self.working_memory = []
    
    def think(self, thought: str) -> str:
        step = {"step": "thought", "content": thought, "timestamp": datetime.now().isoformat()}
        self.trajectory.append(step)
        return thought
    
    def act(self, action: str, params: Dict = None) -> Dict:
        step = {"step": "action", "content": action, "params": params or {}, "timestamp": datetime.now().isoformat()}
        self.trajectory.append(step)
        return step
    
    def observe(self, observation: Any, success: bool = True) -> Dict:
        step = {
            "step": "observation",
            "content": observation if isinstance(observation, str) else str(observation),
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.trajectory.append(step)
        return step
    
    def reflect(self, error: str) -> str:
        error_patterns = {
            "not in": "元素不存在，检查正确的路径或名称",
            "cannot serialize": "序列化失败，检查数据类型是否正确",
            "no such element": "XML 节点不存在，检查 XPath"
        }
        error_lower = error.lower()
        reflection = f"反思: {error_patterns.get(error_lower, '分析错误原因')}"
        step = {"step": "reflection", "content": reflection, "error": error, "timestamp": datetime.now().isoformat()}
        self.trajectory.append(step)
        self.working_memory.append(step)
        return reflection
    
    def get_trajectory(self) -> List[Dict]:
        return self.trajectory
    
    def clear(self):
        self.trajectory = []
        self.working_memory = []


class ValidationError(Exception):
    """参数校验错误"""
    def __init__(self, errors: List[Dict]):
        self.errors = errors
        super().__init__(self._format_errors())
    
    def _format_errors(self) -> str:
        return "\n".join([f"- {e['message']}" for e in self.errors])


class CPTModifier:
    """CPT 修改器 - 基于 XML 的报表修改"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.tree = None
        self.root = None
    
    def load(self) -> bool:
        try:
            self.tree = ET.parse(self.template_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            return False
    
    def save(self, output_path: str) -> bool:
        try:
            self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            return False
    
    # ==================== 筛选组件操作 ====================
    
    def get_filter_components(self) -> List[Dict]:
        """获取筛选组件列表（Label + 输入控件配对）"""
        components = []
        layout = self.root.find('.//ReportParameterAttr//Layout')
        
        if layout is None:
            return components
        
        widgets = list(layout)
        i = 0
        while i < len(widgets):
            widget = widgets[i]
            inner = widget.find('InnerWidget')
            if inner is None:
                i += 1
                continue
            
            widget_class = inner.get('class', '')
            name_elem = inner.find('WidgetName')
            widget_name = name_elem.get('name') if name_elem is not None else ''
            bounds = widget.find('BoundsAttr')
            
            if 'Label' in widget_class:
                value_elem = inner.find('widgetValue/O')
                label_text = (value_elem.text or '').strip() if value_elem is not None else ''
                components.append({
                    "type": "Label",
                    "text": label_text,
                    "code": None,
                    "widget": widget,
                    "bounds": bounds
                })
            else:
                ctrl_type = widget_class.split('.')[-1]
                components.append({
                    "type": ctrl_type,
                    "code": widget_name,
                    "widget": widget,
                    "bounds": bounds,
                    "inner": inner
                })
            i += 1
        
        return components
    
    def get_filter_pairs(self) -> List[Dict]:
        """获取筛选组件对 (Label + 输入控件)"""
        components = self.get_filter_components()
        pairs = []
        i = 0
        while i < len(components) - 1:
            curr = components[i]
            next_comp = components[i + 1] if i + 1 < len(components) else None
            
            if curr['type'] == 'Label' and next_comp and next_comp.get('code'):
                pairs.append({
                    "label": curr['text'],
                    "code": next_comp['code'],
                    "type": next_comp['type'],
                    "label_widget": curr['widget'],
                    "input_widget": next_comp['widget'],
                    "label_bounds": curr['bounds'],
                    "input_bounds": next_comp['bounds']
                })
                i += 2
            else:
                i += 1
        
        return pairs
    
    def remove_filter_component(self, code: str) -> bool:
        """删除筛选组件（删除 Label + 输入控件）"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return False
        
        pairs = self.get_filter_pairs()
        to_remove = []
        
        for pair in pairs:
            if pair['code'] == code:
                to_remove.append(pair['label_widget'])
                to_remove.append(pair['input_widget'])
                break
        
        for widget in to_remove:
            layout.remove(widget)
        
        return len(to_remove) > 0
    
    def add_filter_component(self, label: str, code: str, ctrl_type: str,
                             x: int, y: int, options: Dict = None) -> bool:
        """
        添加筛选组件（复制现有 XML 节点）
        
        Args:
            label: Label 文本
            code: 输入控件名称（参数名）
            ctrl_type: 控件类型 (TextEditor, DateEditor, ComboBox, TreeComboBoxEditor)
            x: Label 的 x 坐标
            y: y 坐标
            options: ComboBox 选项 {"key": "显示值"}
        """
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return False
        
        # 找一个同类型的现有控件作为模板
        template_label = None
        template_input = None
        template_type = ctrl_type
        
        for widget in layout:
            inner = widget.find('InnerWidget')
            if inner is None:
                continue
            
            widget_class = inner.get('class', '')
            
            if 'Label' in widget_class and template_label is None:
                template_label = widget
            elif ctrl_type in widget_class and template_input is None:
                template_input = widget
            elif template_input is None and 'TextEditor' in widget_class:
                # 找不到同类型，用 TextEditor 作为模板
                template_input = widget
        
        if template_label is None or template_input is None:
            return False
        
        # 深拷贝 Label
        new_label = copy.deepcopy(template_label)
        new_label_inner = new_label.find('InnerWidget')
        
        # 修改 Label 名称
        new_label_name = new_label_inner.find('WidgetName')
        if new_label_name is not None:
            new_label_name.set('name', f'label_{code}')
        
        # 修改 Label 文本
        new_label_value = new_label_inner.find('widgetValue/O')
        if new_label_value is not None:
            new_label_value.text = label
        
        # 修改 Label 位置
        new_label_bounds = new_label.find('BoundsAttr')
        if new_label_bounds is not None:
            new_label_bounds.set('x', str(x))
            new_label_bounds.set('y', str(y))
        
        # 深拷贝输入控件
        new_input = copy.deepcopy(template_input)
        new_input_inner = new_input.find('InnerWidget')
        
        # 修改控件类型
        new_input_inner.set('class', f'com.fr.form.ui.{ctrl_type}')
        
        # 修改控件名称
        new_input_name = new_input_inner.find('WidgetName')
        if new_input_name is not None:
            new_input_name.set('name', code)
        
        # 计算输入控件位置（Label 后面）
        label_width = int(new_label_bounds.get('width', '70')) if new_label_bounds is not None else 70
        input_x = x + label_width + 10
        
        new_input_bounds = new_input.find('BoundsAttr')
        if new_input_bounds is not None:
            new_input_bounds.set('x', str(input_x))
            new_input_bounds.set('y', str(y))
        
        # 添加选项（ComboBox）
        if options and ctrl_type == 'ComboBox':
            # 移除现有选项
            existing_dict = new_input_inner.find('Dictionary')
            if existing_dict is not None:
                new_input_inner.remove(existing_dict)
            
            # 添加新选项
            dict_elem = ET.SubElement(new_input_inner, 'Dictionary')
            dict_elem.set('class', 'com.fr.data.impl.CustomDictionary')
            dict_attr = ET.SubElement(dict_elem, 'CustomDictAttr')
            for key, value in options.items():
                dict_item = ET.SubElement(dict_attr, 'Dict')
                dict_item.set('key', str(key))
                dict_item.set('value', str(value))
        
        # 添加到布局
        layout.append(new_label)
        layout.append(new_input)
        
        return True
    
    def recalculate_filter_positions(self):
        """重新计算所有筛选组件的位置"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return
        
        pairs = self.get_filter_pairs()
        
        # 布局参数
        START_X = 10
        START_Y = 10
        LABEL_WIDTH = 70
        INPUT_WIDTH = 135
        GAP = 10
        ROW_GAP = 40
        MAX_PER_ROW = 5
        
        for i, pair in enumerate(pairs):
            row = i // MAX_PER_ROW
            col = i % MAX_PER_ROW
            
            label_x = START_X + col * (LABEL_WIDTH + INPUT_WIDTH + GAP * 2)
            y = START_Y + row * ROW_GAP
            input_x = label_x + LABEL_WIDTH + GAP
            
            # 更新 Label 位置
            label_bounds = pair['label_widget'].find('BoundsAttr')
            if label_bounds is not None:
                label_bounds.set('x', str(label_x))
                label_bounds.set('y', str(y))
            
            # 更新输入控件位置
            input_bounds = pair['input_widget'].find('BoundsAttr')
            if input_bounds is not None:
                input_bounds.set('x', str(input_x))
                input_bounds.set('y', str(y))
    
    # ==================== 数据列操作 ====================
    
    def get_data_columns(self) -> Tuple[List[Dict], List[Dict]]:
        """获取数据列（表头行 + 数据行）"""
        cell_list = self.root.find('.//CellElementList')
        if cell_list is None:
            return [], []
        
        cells = list(cell_list)
        
        # 按行分组
        rows = {}
        for cell in cells:
            r = int(cell.get('r', 0))
            if r not in rows:
                rows[r] = []
            rows[r].append(cell)
        
        header_cells = sorted(rows.get(0, []), key=lambda c: int(c.get('c', 0)))
        data_cells = sorted(rows.get(1, []), key=lambda c: int(c.get('c', 0)))
        
        # 解析表头
        headers = []
        for cell in header_cells:
            o = cell.find('O')
            headers.append({
                "column": int(cell.get('c', 0)),
                "value": o.text if o is not None else '',
                "style_index": int(cell.get('s', '0')),
                "cell": cell
            })
        
        # 解析数据行
        data_cols = []
        for cell in data_cells:
            o = cell.find('O')
            attrs = o.find('Attributes') if o is not None else None
            data_cols.append({
                "column": int(cell.get('c', 0)),
                "field": attrs.get('columnName') if attrs is not None else '',
                "data_source": attrs.get('dsName') if attrs is not None else '',
                "style_index": int(cell.get('s', '0')),
                "cell": cell
            })
        
        return headers, data_cols
    
    def update_data_columns(self, columns: List[Dict], data_source: str = None) -> bool:
        """
        更新数据列（支持增删）
        
        Args:
            columns: 列配置 [{name, field}]
            data_source: 数据源名称
        """
        cell_list = self.root.find('.//CellElementList')
        if cell_list is None:
            return False
        
        headers, data_cols = self.get_data_columns()
        existing_count = len(headers)
        target_count = len(columns)
        
        # 情况1：列数相同，直接更新
        if existing_count == target_count:
            for i, col in enumerate(columns):
                if i < len(headers):
                    # 更新表头
                    o = headers[i]['cell'].find('O')
                    if o is not None:
                        o.text = col.get('name', '')
                
                if i < len(data_cols):
                    # 更新数据列
                    o = data_cols[i]['cell'].find('O')
                    if o is not None:
                        attrs = o.find('Attributes')
                        if attrs is not None:
                            attrs.set('columnName', col.get('field', ''))
                            if data_source:
                                attrs.set('dsName', data_source)
        
        # 情况2：列数减少，删除多余
        elif existing_count > target_count:
            # 更新保留的列
            for i, col in enumerate(columns):
                if i < len(headers):
                    o = headers[i]['cell'].find('O')
                    if o is not None:
                        o.text = col.get('name', '')
                
                if i < len(data_cols):
                    o = data_cols[i]['cell'].find('O')
                    if o is not None:
                        attrs = o.find('Attributes')
                        if attrs is not None:
                            attrs.set('columnName', col.get('field', ''))
                            if data_source:
                                attrs.set('dsName', data_source)
            
            # 删除多余的列
            for i in range(target_count, existing_count):
                if i < len(headers):
                    cell_list.remove(headers[i]['cell'])
                if i < len(data_cols):
                    cell_list.remove(data_cols[i]['cell'])
        
        # 情况3：列数增加，复制添加
        elif existing_count < target_count:
            # 更新现有列
            for i in range(min(existing_count, target_count)):
                if i < len(headers):
                    o = headers[i]['cell'].find('O')
                    if o is not None:
                        o.text = columns[i].get('name', '')
                
                if i < len(data_cols):
                    o = data_cols[i]['cell'].find('O')
                    if o is not None:
                        attrs = o.find('Attributes')
                        if attrs is not None:
                            attrs.set('columnName', columns[i].get('field', ''))
                            if data_source:
                                attrs.set('dsName', data_source)
            
            # 复制添加新列
            if headers and data_cols:
                last_header = headers[-1]['cell']
                last_data = data_cols[-1]['cell']
                
                for i in range(existing_count, target_count):
                    col = columns[i]
                    
                    # 复制表头单元格
                    new_header = copy.deepcopy(last_header)
                    new_header.set('c', str(i))
                    o = new_header.find('O')
                    if o is not None:
                        o.text = col.get('name', '')
                    cell_list.append(new_header)
                    
                    # 复制数据单元格
                    new_data = copy.deepcopy(last_data)
                    new_data.set('c', str(i))
                    o = new_data.find('O')
                    if o is not None:
                        attrs = o.find('Attributes')
                        if attrs is not None:
                            attrs.set('columnName', col.get('field', ''))
                            if data_source:
                                attrs.set('dsName', data_source)
                    cell_list.append(new_data)
        
        return True
    
    # ==================== 数据源操作 ====================
    
    def get_data_sources(self) -> List[Dict]:
        """获取数据源列表"""
        table_data_map = self.root.find('.//TableDataMap')
        if table_data_map is None:
            return []
        
        data_sources = []
        for td in table_data_map.findall('TableData'):
            ds = {
                "name": td.get('name'),
                "type": td.get('class', '').split('.')[-1],
                "element": td
            }
            
            # Class 数据源
            class_attr = td.find('ClassTableDataAttr')
            if class_attr is not None:
                ds['class_name'] = class_attr.get('className')
                ds['type'] = 'ClassTableData'
            
            # 数据库数据源
            conn = td.find('Connection')
            if conn is not None:
                db_name = conn.find('DatabaseName')
                ds['database'] = db_name.text if db_name is not None else ''
                ds['type'] = 'DBTableData'
            
            # 参数
            params = td.find('Parameters')
            if params is not None:
                ds['parameters'] = []
                for p in params.findall('Parameter'):
                    attrs = p.find('Attributes')
                    name = attrs.get('name') if attrs is not None else ''
                    default = p.find('O')
                    ds['parameters'].append({
                        "name": name,
                        "default": default.text if default is not None else ''
                    })
            
            data_sources.append(ds)
        
        return data_sources
    
    def update_data_source(self, ds_name: str, params: Dict[str, Any]) -> bool:
        """
        更新数据源参数
        
        Args:
            ds_name: 数据源名称
            params: 参数 {name: default_value}
        """
        table_data_map = self.root.find('.//TableDataMap')
        if table_data_map is None:
            return False
        
        # 找到数据源
        ds_element = None
        for td in table_data_map.findall('TableData'):
            if td.get('name') == ds_name:
                ds_element = td
                break
        
        if ds_element is None:
            return False
        
        # 获取或创建 Parameters 节点
        params_elem = ds_element.find('Parameters')
        if params_elem is None:
            params_elem = ET.SubElement(ds_element, 'Parameters')
        
        # 更新参数
        existing_params = {}
        for p in params_elem.findall('Parameter'):
            attrs = p.find('Attributes')
            if attrs is not None:
                name = attrs.get('name')
                existing_params[name] = p
        
        for param_name, default_value in params.items():
            if param_name in existing_params:
                # 更新现有参数
                o = existing_params[param_name].find('O')
                if o is not None:
                    o.text = str(default_value) if default_value else ''
            else:
                # 添加新参数
                new_param = ET.SubElement(params_elem, 'Parameter')
                attrs = ET.SubElement(new_param, 'Attributes')
                attrs.set('name', param_name)
                o = ET.SubElement(new_param, 'O')
                o.text = str(default_value) if default_value else ''
        
        return True


class ReportBuilderAgent:
    """报表生成 Agent v2.0"""
    
    def __init__(self, template_dir: str = "examples", memory_dir: str = "memory"):
        self.template_dir = Path(template_dir)
        self.memory = MemoryManager(memory_dir)
        self.react = ReActEngine()
        
        self.template_map = {
            "管理分析": "FinanceCreditContractAnalysis.cpt",
            "明细": "FinanceCreditContractAnalysisDetail.cpt"
        }
    
    def validate_params(self, filter_components: List[Dict], data_source_params: Dict) -> Tuple[bool, List[Dict]]:
        """
        校验参数完整性
        
        规则：数据源参数只能多不能少
        - 参数有筛选组件 → 绑定
        - 参数有默认值 → 使用默认值
        - 参数无筛选组件且无默认值 → 错误
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        filter_codes = {c['code'] for c in filter_components}
        
        for param_name, default_value in data_source_params.items():
            has_filter = param_name in filter_codes
            has_default = default_value is not None and default_value != '' and default_value != []
            
            if not has_filter and not has_default:
                errors.append({
                    "type": "missing_binding",
                    "param": param_name,
                    "message": f"数据源参数 '{param_name}' 没有对应的筛选组件，且没有默认值",
                    "suggestion": f"添加筛选组件 {{\"code\": \"{param_name}\", ...}} 或设置默认值"
                })
        
        return len(errors) == 0, errors
    
    def build_report(
        self,
        report_type: str,
        filter_components: List[Dict],
        data_columns: List[Dict],
        data_source: Dict = None,
        output_path: str = None
    ) -> Dict:
        """
        生成报表
        
        Args:
            report_type: 报表类型 ("管理分析" 或 "明细")
            filter_components: 筛选组件 [{label, code, type, options?}]
            data_columns: 数据列 [{name, field}]
            data_source: 数据源配置 {name, type, class_name/database, parameters: {name: default}}
            output_path: 输出路径
        """
        
        result = {
            "success": False,
            "output_file": None,
            "trajectory": [],
            "error": None,
            "validation_errors": []
        }
        
        try:
            # ========== Thought 1: 分析需求 ==========
            self.react.think(f"分析需求: 报表类型={report_type}, 筛选组件={len(filter_components)}个, 数据列={len(data_columns)}列")
            
            # ========== 校验参数 ==========
            if data_source and data_source.get('parameters'):
                is_valid, errors = self.validate_params(filter_components, data_source['parameters'])
                if not is_valid:
                    result['validation_errors'] = errors
                    raise ValidationError(errors)
            
            # ========== Action 1: 加载模板 ==========
            self.react.act("加载模板", {"type": report_type})
            
            template_name = self.template_map.get(report_type)
            if not template_name:
                raise ValueError(f"未知的报表类型: {report_type}")
            
            template_path = self.template_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {template_path}")
            
            modifier = CPTModifier(str(template_path))
            if not modifier.load():
                raise RuntimeError("模板加载失败")
            
            self.react.observe(f"模板加载成功: {template_name}")
            
            # ========== Thought 2: 分析差异 ==========
            existing_pairs = modifier.get_filter_pairs()
            self.react.think(f"现有筛选组件: {len(existing_pairs)}对, 需要: {len(filter_components)}对")
            
            # ========== Action 2: 修改筛选组件 ==========
            self.react.act("修改筛选组件", {"target": len(filter_components)})
            
            existing_codes = {p['code'] for p in existing_pairs}
            target_codes = {c['code'] for c in filter_components}
            
            to_remove = existing_codes - target_codes
            to_add = target_codes - existing_codes
            
            # 删除多余的
            for code in to_remove:
                modifier.remove_filter_component(code)
                self.react.observe(f"删除组件: {code}")
            
            # 添加缺少的
            for comp in filter_components:
                if comp['code'] in to_add:
                    # 计算位置
                    existing = modifier.get_filter_pairs()
                    new_index = len(existing)
                    row = new_index // 5
                    col = new_index % 5
                    x = 10 + col * 220
                    y = 10 + row * 40
                    
                    modifier.add_filter_component(
                        label=comp['label'],
                        code=comp['code'],
                        ctrl_type=comp.get('type', 'TextEditor'),
                        x=x, y=y,
                        options=comp.get('options')
                    )
                    self.react.observe(f"添加组件: {comp['label']} ({comp['code']})")
            
            # 重新计算位置
            modifier.recalculate_filter_positions()
            self.react.observe("筛选组件位置已调整")
            
            # ========== Action 3: 更新数据源 ==========
            if data_source:
                self.react.act("更新数据源", {"name": data_source.get('name')})
                
                ds_name = data_source.get('name')
                params = data_source.get('parameters', {})
                
                if modifier.update_data_source(ds_name, params):
                    self.react.observe(f"数据源更新成功: {ds_name}, 参数: {len(params)}个")
                else:
                    self.react.observe("数据源更新失败", success=False)
            
            # ========== Action 4: 更新数据列 ==========
            self.react.act("更新数据列", {"columns": len(data_columns)})
            
            headers, data_cols = modifier.get_data_columns()
            ds_name = data_source.get('name') if data_source else None
            
            if modifier.update_data_columns(data_columns, ds_name):
                self.react.observe(f"数据列更新成功: {len(data_columns)}列 (原{len(headers)}列)")
            else:
                self.react.observe("数据列更新失败", success=False)
            
            # ========== Action 5: 保存输出 ==========
            if not output_path:
                output_path = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
            
            self.react.act("保存报表", {"path": output_path})
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if modifier.save(output_path):
                self.react.observe(f"报表保存成功: {output_path}")
                result['success'] = True
                result['output_file'] = output_path
                
                self.memory.record_success("report_build", {
                    "report_type": report_type,
                    "filter_count": len(filter_components),
                    "column_count": len(data_columns)
                })
            else:
                raise RuntimeError("报表保存失败")
            
        except ValidationError as e:
            result['error'] = str(e)
            self.react.reflect(str(e))
            self.memory.record_correction("validation", str(e), "检查参数绑定", {"report_type": report_type})
        
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            self.react.reflect(error_msg)
            self.memory.record_correction(
                error_type=type(e).__name__,
                error_msg=error_msg,
                fix="待分析",
                context={"report_type": report_type}
            )
        
        result['trajectory'] = self.react.get_trajectory()
        return result


# 便捷函数
def create_agent(template_dir: str = "examples", memory_dir: str = "memory") -> ReportBuilderAgent:
    return ReportBuilderAgent(template_dir, memory_dir)


if __name__ == "__main__":
    print("=== FineReport Builder Agent v2.0 测试 ===\n")
    
    agent = create_agent()
    
    # 测试配置
    config = {
        "report_type": "管理分析",
        "filter_components": [
            {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
            {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
            {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"},
            {"label": "区域", "code": "region", "type": "ComboBox", "options": {"east": "华东", "south": "华南"}}
        ],
        "data_columns": [
            {"name": "合同编号", "field": "contractNo"},
            {"name": "合同名称", "field": "contractName"},
            {"name": "金额", "field": "amount"},
            {"name": "状态", "field": "status"},
            {"name": "新增列", "field": "newField"}  # 测试新增列
        ],
        "data_source": {
            "name": "CreditContractDetailData",
            "type": "class",
            "parameters": {
                "orgId": "",           # 从筛选组件获取
                "startDate": "",       # 从筛选组件获取
                "endDate": "",         # 从筛选组件获取
                "region": "",          # 从筛选组件获取
                "defaultParam": "值"   # 有默认值
            }
        }
    }
    
    result = agent.build_report(**config)
    
    print("\n=== 结果 ===")
    print(f"成功: {result['success']}")
    print(f"输出文件: {result['output_file']}")
    if result['error']:
        print(f"错误: {result['error']}")
    if result['validation_errors']:
        print(f"校验错误: {result['validation_errors']}")
    
    print("\n=== 轨迹 ===")
    for step in result['trajectory'][-10:]:
        print(f"[{step['step']}] {step['content'][:80]}")