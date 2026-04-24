"""CPT 报表生成与修改工具 — 命令行入口

用法:
  # 创建新报表
  python cpt_tools/generate.py --config config.json --output outputs/report.cpt

  # 修改现有报表
  python cpt_tools/generate.py --modify outputs/existing.cpt \
      --add-filters '[{"label":"区域","code":"region","type":"ComboBox"}]' \
      --add-columns '[{"header":"区域","field":"region"}]' \
      --output outputs/modified.cpt

  # 从标准输入读取配置
  echo '{"title":"测试","data_sources":[...],"filter_controls":[...],"cells":[...]}' | \
      python cpt_tools/generate.py --stdin --output outputs/report.cpt
"""
import argparse
import copy
import json
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parsers.cpt_generator import CPTGenerator


def build_config_from_args(args):
    """从命令行参数构建配置"""
    if args.stdin:
        data = sys.stdin.read()
        return json.loads(data)

    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 从单独参数构建
    config = {
        "title": args.title or "新建报表",
        "sheet_name": args.sheet or "Sheet1",
        "data_sources": [],
        "filter_controls": [],
        "cells": [],
        "styles": [],
    }

    # 数据源
    if args.datasource:
        ds = json.loads(args.datasource)
        config["data_sources"].append(ds)

    # 筛选组件
    if args.filters:
        config["filter_controls"] = json.loads(args.filters)

    # 展示列
    if args.columns:
        columns = json.loads(args.columns)
        ds_name = config["data_sources"][0]["name"] if config["data_sources"] else "data"

        for i, col in enumerate(columns):
            header = col.get("header", col.get("name", ""))
            field = col.get("field", "")
            is_amount = col.get("is_amount", False)

            # 判断是否序号列
            if header == "序号" and not field:
                config["cells"].append({
                    "column": i, "row": 0, "value": "序号", "style_index": 0
                })
                config["cells"].append({
                    "column": i, "row": 1, "value_type": "Formula",
                    "value": "seq()", "style_index": 2
                })
            else:
                config["cells"].append({
                    "column": i, "row": 0, "value": header, "style_index": 1
                })
                config["cells"].append({
                    "column": i, "row": 1, "value_type": "DSColumn",
                    "data_source": ds_name, "column_name": field,
                    "expand_dir": 0,
                    "style_index": 3 if is_amount else 2
                })

    # 动态列
    if args.dynamic_columns:
        headers = [col.get("header", col.get("name", "")) for col in columns]
        config["enable_dynamic_columns"] = True
        config["column_headers"] = headers

    return config


def modify_cpt(cpt_path, args):
    """修改现有 CPT 文件"""
    import xml.etree.ElementTree as ET

    tree = ET.parse(cpt_path)
    root = tree.getroot()

    # 添加筛选组件
    if args.add_filters:
        filters = json.loads(args.add_filters)
        layout = root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            print("❌ 找不到参数面板布局节点")
            sys.exit(1)

        # 收集现有组件数量
        existing_widgets = list(layout.findall('Widget'))
        next_index = len([w for w in existing_widgets
                         if w.find('.//WidgetName')
                         and w.find('.//WidgetName').get('name', '').startswith('label_')])

        # 布局常量
        LABEL_WIDTH = 89
        INPUT_WIDTH = 135
        LABEL_INPUT_GAP = 4
        PAIR_GAP = 4
        ROW_HEIGHT = 28
        ROW_GAP = 8
        PAIRS_PER_ROW = 5
        START_X = 10
        START_Y = 10

        total_widgets = len([w for w in existing_widgets
                            if w.find('.//WidgetName')
                            and not w.find('.//WidgetName').get('name', '').startswith('label_')
                            and w.find('.//WidgetName').get('name') != 'para'])

        for i, filt in enumerate(filters):
            idx = total_widgets + i
            row = idx // PAIRS_PER_ROW
            col = idx % PAIRS_PER_ROW
            pair_width = LABEL_WIDTH + LABEL_INPUT_GAP + INPUT_WIDTH
            x_label = START_X + col * (pair_width + PAIR_GAP)
            x_input = x_label + LABEL_WIDTH + LABEL_INPUT_GAP
            y = START_Y + row * (ROW_HEIGHT + ROW_GAP)

            # 创建 Label
            label_widget = ET.Element('Widget')
            label_widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
            inner = ET.SubElement(label_widget, 'InnerWidget')
            inner.set('class', 'com.fr.form.ui.Label')
            name = ET.SubElement(inner, 'WidgetName')
            name.set('name', f'label_{next_index + i}')
            wv = ET.SubElement(inner, 'widgetValue')
            o = ET.SubElement(wv, 'O')
            o.text = filt['label']
            bounds = ET.SubElement(label_widget, 'BoundsAttr')
            bounds.set('x', str(x_label))
            bounds.set('y', str(y))
            bounds.set('width', str(LABEL_WIDTH))
            bounds.set('height', str(ROW_HEIGHT))
            layout.append(label_widget)

            # 创建输入控件
            input_widget = ET.Element('Widget')
            input_widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
            inner = ET.SubElement(input_widget, 'InnerWidget')
            inner.set('class', f"com.fr.form.ui.{filt.get('type', 'TextEditor')}")
            name = ET.SubElement(inner, 'WidgetName')
            name.set('name', filt['code'])
            wv = ET.SubElement(inner, 'widgetValue')
            o = ET.SubElement(wv, 'O')
            o.text = ''
            bounds = ET.SubElement(input_widget, 'BoundsAttr')
            bounds.set('x', str(x_input))
            bounds.set('y', str(y))
            bounds.set('width', str(INPUT_WIDTH))
            bounds.set('height', str(ROW_HEIGHT))
            layout.append(input_widget)

    # 添加/替换数据列
    if args.add_columns:
        columns = json.loads(args.add_columns)
        cell_list = root.find('.//CellElementList')
        if cell_list is None:
            print("❌ 找不到单元格列表节点")
            sys.exit(1)

        # 移除旧数据行单元格
        for cell in list(cell_list):
            r = int(cell.get('r', 0))
            if r >= 1:  # 删除数据行
                cell_list.remove(cell)

        # 保留表头行的单元格，删除并重建
        for cell in list(cell_list):
            cell_list.remove(cell)

        ds_name = args.datasource_name or _get_first_ds_name(root)

        for i, col in enumerate(columns):
            header = col.get("header", col.get("name", ""))
            field = col.get("field", "")
            is_amount = col.get("is_amount", False)

            # 表头
            header_cell = ET.Element('C')
            header_cell.set('c', str(i))
            header_cell.set('r', '0')
            header_cell.set('s', '0' if i == 0 else '1')
            o = ET.SubElement(header_cell, 'O')
            o.text = header
            ET.SubElement(header_cell, 'PrivilegeControl')
            expand = ET.SubElement(header_cell, 'Expand')
            ET.SubElement(expand, 'cellSortAttr')
            cell_list.append(header_cell)

            # 数据行
            data_cell = ET.Element('C')
            data_cell.set('c', str(i))
            data_cell.set('r', '1')
            data_cell.set('s', '3' if is_amount else '2')

            if header == "序号" and not field:
                o = ET.SubElement(data_cell, 'O')
                o.set('t', 'XMLable')
                o.set('class', 'com.fr.base.Formula')
                o.text = 'seq()'
            else:
                o = ET.SubElement(data_cell, 'O')
                o.set('t', 'DSColumn')
                attrs = ET.SubElement(o, 'Attributes')
                attrs.set('dsName', ds_name)
                attrs.set('columnName', field)

            ET.SubElement(data_cell, 'PrivilegeControl')
            expand = ET.SubElement(data_cell, 'Expand')
            expand.set('dir', '0')
            ET.SubElement(expand, 'cellSortAttr')
            cell_list.append(data_cell)

    tree.write(args.output, encoding='UTF-8', xml_declaration=True)
    print(f"✅ 修改完成: {args.output}")


def _get_first_ds_name(root):
    """获取第一个数据源名称"""
    td = root.find('.//TableData')
    return td.get('name') if td is not None else 'data'


def main():
    parser = argparse.ArgumentParser(description="CPT 报表生成与修改工具")
    parser.add_argument("--config", help="JSON 配置文件路径")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取配置")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--title", help="报表标题")
    parser.add_argument("--sheet", help="Sheet 名称")
    parser.add_argument("--datasource", help="数据源 JSON")
    parser.add_argument("--filters", help="筛选组件 JSON 数组")
    parser.add_argument("--columns", help="展示列 JSON 数组")
    parser.add_argument("--dynamic-columns", action="store_true", help="启用动态列")

    # 修改模式
    parser.add_argument("--modify", help="要修改的 CPT 文件路径")
    parser.add_argument("--add-filters", help="添加筛选组件 JSON 数组")
    parser.add_argument("--add-columns", help="添加/替换数据列 JSON 数组")
    parser.add_argument("--datasource-name", help="数据源名称（修改模式用）")

    args = parser.parse_args()

    if args.modify:
        if not args.add_filters and not args.add_columns:
            parser.error("--modify 需要搭配 --add-filters 或 --add-columns")
        if not args.output:
            args.output = args.modify.replace('.cpt', '_modified.cpt')
        modify_cpt(args.modify, args)
        return

    if not args.config and not args.stdin and not args.datasource:
        parser.error("需要 --config、--stdin 或 --datasource 参数")

    # 构建配置
    config = build_config_from_args(args)

    # 确保默认值
    config.setdefault("styles", [])

    # 生成 CPT
    generator = CPTGenerator()
    cpt_content = generator.generate(config)

    # 输出路径
    if not args.output:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = config.get("title", "report").replace("/", "_").replace("\\", "_")
        args.output = f"outputs/{safe_title}_{ts}.cpt"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cpt_content)

    # 统计信息
    ds_count = len(config.get("data_sources", []))
    filter_count = len(config.get("filter_controls", []))
    cell_count = len(config.get("cells", []))
    col_count = cell_count // 2  # 表头 + 数据行

    print(f"\n✅ 报表创建成功: {output_path}")
    print(f"📊 数据源: {ds_count} 个")
    print(f"🔍 筛选组件: {filter_count} 对")
    print(f"📋 展示列: {col_count} 列")
    print(f"📄 文件大小: {len(cpt_content)} 字符")


if __name__ == "__main__":
    main()
