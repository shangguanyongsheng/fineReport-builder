"""FineReport Builder Web 服务

提供 CPT 文件分析、生成、验证和 ClassTableData 交互测试。
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import re
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
os.sys.path.insert(0, str(PROJECT_ROOT))

from parsers.cpt_parser import CPTParser
from parsers.class_table_data import ClassTableDataParser

app = Flask(__name__)
CORS(app)

# 输出目录
OUTPUT_FOLDER = PROJECT_ROOT / 'outputs'
OUTPUT_FOLDER.mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'] = str(OUTPUT_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


# ============ 页面路由 ============

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/cpt-analyze')
def cpt_analyze_page():
    """CPT 分析页面"""
    return render_template('cpt_analyze.html')


@app.route('/class-test')
def class_test_page():
    """ClassTableData 测试页面"""
    return render_template('class_test.html')


# ============ API 接口 ============

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


@app.route('/api/view/<filename>')
def view_file(filename):
    """查看文件（HTML）"""
    return send_from_directory(OUTPUT_FOLDER, filename)


@app.route('/api/list/files')
def list_files():
    """列出输出文件"""
    outputs = [
        {
            'name': f.name,
            'size': f.stat().st_size,
            'time': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        }
        for f in OUTPUT_FOLDER.iterdir() if f.is_file()
    ]
    return jsonify({'outputs': sorted(outputs, key=lambda x: x['time'], reverse=True)})


# ============ V2 报表生成接口 ============

@app.route('/api/v2/generate', methods=['POST'])
def generate_report_v2():
    """V2 报表生成接口"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("收到 V2 报表生成请求")

    data = request.json
    logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        datasource = data.get('datasource', {})
        column_mapping = data.get('column_mapping', {})
        filter_components = data.get('filter_components', [])
        report_info = data.get('report', {})
        report_type = data.get('report_type', 'analysis')
        enable_dynamic_columns = data.get('enable_dynamic_columns', False)

        logger.info(f"数据源类型: {datasource.get('type')}")
        logger.info(f"报表类型: {report_type}")
        logger.info(f"列映射: {column_mapping}")
        logger.info(f"筛选组件数量: {len(filter_components)}")

        cpt_config = {
            'title': report_info.get('title', '新建报表'),
            'sheet_name': report_info.get('sheet_name', 'Sheet1'),
            'report_type': report_type,
            'data_sources': [],
            'filter_controls': [],
            'cells': [],
            'enable_dynamic_columns': enable_dynamic_columns
        }

        # 数据源配置
        if datasource.get('type') == 'database':
            sql = datasource.get('sql', '')
            params = extract_params_from_sql(sql)
            logger.info(f"SQL 参数: {params}")

            cpt_config['data_sources'].append({
                'name': datasource.get('name', 'main_data'),
                'type': 'DBTableData',
                'database': datasource.get('database', ''),
                'sql': sql,
                'parameters': params
            })
            logger.info(f"数据库数据源已配置: {datasource.get('name')}")

        elif datasource.get('type') == 'class':
            param_template = datasource.get('parameter_template', [])
            params = []
            if isinstance(param_template, list) and len(param_template) > 0:
                for item in param_template:
                    if isinstance(item, dict):
                        for param_name, param_value in item.items():
                            if param_value is None:
                                default_value = ''
                            elif isinstance(param_value, str):
                                default_value = param_value
                            elif isinstance(param_value, (dict, list)):
                                default_value = json.dumps(param_value, ensure_ascii=False)
                            else:
                                default_value = str(param_value)
                            params.append({'name': param_name, 'default': default_value})

            elif isinstance(param_template, dict) and len(param_template) > 0:
                for k, v in param_template.items():
                    if v is None:
                        default_value = ''
                    elif isinstance(v, str):
                        default_value = v
                    elif isinstance(v, (dict, list)):
                        default_value = json.dumps(v, ensure_ascii=False)
                    else:
                        default_value = str(v)
                    params.append({'name': k, 'default': default_value})
            else:
                for comp in filter_components:
                    code = comp.get('code')
                    if code:
                        params.append({'name': code, 'default': ''})
                logger.info(f"从筛选组件自动推断入参: {[p['name'] for p in params]}")
            logger.info(f"原始 parameter_template: {param_template}")
            logger.info(f"处理后的 params: {params}")

            for p in params:
                logger.info(f"  参数: {p['name']} = {p['default'][:50] if p['default'] else '(空)'}")

            return_fields = datasource.get('return_fields', [])
            if isinstance(return_fields, list) and len(return_fields) > 0:
                if isinstance(return_fields[0], dict):
                    return_fields = [f.get('name', '') for f in return_fields if isinstance(f, dict)]
            logger.info(f"Class 出参: {return_fields}")

            cpt_config['data_sources'].append({
                'name': datasource.get('name', 'main_data'),
                'type': 'ClassTableData',
                'class_name': datasource.get('class_name', ''),
                'return_fields': return_fields,
                'parameters': params
            })
            logger.info(f"Class 数据源已配置: {datasource.get('name')}")

        # 筛选组件配置
        logger.info("配置筛选组件...")
        for i, comp in enumerate(filter_components):
            ctrl = {
                'name': comp.get('code', f'param_{i}'),
                'label': comp.get('label', ''),
                'type': comp.get('type', 'TextEditor'),
                'default': comp.get('default_value', ''),
                'x': 100 + (i % 5) * 220,
                'y': 10 + (i // 5) * 50
            }
            cpt_config['filter_controls'].append(ctrl)
            logger.debug(f"组件 {i}: {ctrl}")
        logger.info(f"筛选组件配置完成，共 {len(cpt_config['filter_controls'])} 个")

        # 单元格配置
        logger.info("配置单元格...")
        styles = data.get('styles', [])
        logger.info(f"样式配置: {len(styles)} 个")
        styles = normalize_styles(styles)

        if not styles:
            styles = [
                {
                    "name": "表头样式",
                    "horizontal_alignment": "2",
                    "font": {"name": "宋体", "style": "0", "size": "80"},
                    "background": "-1447425",
                    "border": True
                }
            ]
            logger.info("使用默认样式")

        cpt_config['styles'] = styles
        column_headers = []

        row = 0
        for col_letter, mapping_value in column_mapping.items():
            col_num = parse_col_letter(col_letter)
            if isinstance(mapping_value, dict):
                header_name = mapping_value.get('header', mapping_value.get('field', ''))
                field_name = mapping_value.get('field', '')
            else:
                header_name = mapping_value
                field_name = mapping_value

            if not header_name:
                continue
            column_headers.append(header_name)
            cpt_config['cells'].append({
                'column': col_num,
                'row': row,
                'value': header_name,
                'style_index': 1
            })
            logger.debug(f"表头单元格: {col_letter}({col_num}) -> {header_name}")

        row = 1
        ds_name = cpt_config['data_sources'][0]['name'] if cpt_config['data_sources'] else 'data'
        for col_letter, mapping_value in column_mapping.items():
            col_num = parse_col_letter(col_letter)
            if isinstance(mapping_value, dict):
                field_name = mapping_value.get('field', '')
            else:
                field_name = mapping_value

            if not field_name:
                cpt_config['cells'].append({
                    'column': col_num,
                    'row': row,
                    'value_type': 'Formula',
                    'value': 'seq()',
                    'style_index': 2
                })
                logger.debug(f"序号公式列: {col_letter}({col_num}) -> seq()")
                continue

            is_amount = any(kw in field_name.lower() for kw in ['amount', 'money', '金额', 'price', '费用'])
            cpt_config['cells'].append({
                'column': col_num,
                'row': row,
                'value_type': 'DSColumn',
                'data_source': ds_name,
                'column_name': field_name,
                'expand_dir': 0,
                'style_index': 3 if is_amount else 2
            })
            logger.debug(f"数据单元格: {col_letter}({col_num}) -> {field_name}")

        logger.info(f"单元格配置完成，共 {len(cpt_config['cells'])} 个")

        if enable_dynamic_columns and column_headers:
            cpt_config['column_headers'] = column_headers
            logger.info(f"启用动态列，列名: {column_headers}")

        row_height = data.get('row_height', {})
        column_width = data.get('column_width', {})
        if row_height:
            cpt_config['row_height'] = row_height
        if column_width:
            cpt_config['column_width'] = column_width

        # 生成 CPT 文件
        logger.info("开始生成 CPT 文件...")
        from parsers.cpt_generator import CPTGenerator
        generator = CPTGenerator()
        cpt_content = generator.generate(cpt_config)
        logger.info(f"CPT 文件生成成功，大小: {len(cpt_content)} 字符")

        output_filename = f"{report_info.get('title', 'report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
        output_path = OUTPUT_FOLDER / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cpt_content)
        logger.info(f"文件已保存: {output_path}")
        logger.info("报表生成完成!")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'output_file': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'config': cpt_config
        })

    except Exception as e:
        logger.error(f"生成失败: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        return jsonify({'error': str(e)}), 500


# ============ 辅助函数 ============

def extract_params_from_sql(sql):
    """从 SQL 中提取参数名"""
    params = re.findall(r'\$\{(\w+)\}', sql)
    return [{'name': p, 'default': ''} for p in params]


def parse_col_letter(col):
    """Excel 列字母转数字（A=0, Z=25, AA=26, AB=27...）"""
    result = 0
    for ch in col.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def normalize_styles(styles):
    """规范化样式配置，确保所有值都是字符串类型"""
    if not styles:
        return styles

    normalized = []
    for style in styles:
        norm_style = {}
        for key in ['name', 'horizontal_alignment', 'format']:
            if key in style:
                norm_style[key] = str(style[key])
        if 'border' in style:
            norm_style['border'] = bool(style['border'])
        if 'is_default' in style:
            norm_style['is_default'] = bool(style['is_default'])
        if 'background' in style:
            norm_style['background'] = str(style['background']) if style['background'] is not None else None
        if 'font' in style:
            font = style['font']
            norm_font = {}
            for fk in ['name', 'style', 'size', 'color']:
                if fk in font:
                    norm_font[fk] = str(font[fk])
            norm_style['font'] = norm_font
        normalized.append(norm_style)
    return normalized


# ============ 启动入口 ============

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FineReport Builder Web 服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=5002, help='端口号')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         FineReport Builder Web 服务                       ║
╠══════════════════════════════════════════════════════════╣
║  地址: http://{args.host}:{args.port}                       ║
║  功能:                                                    ║
║    - CPT 文件分析                                         ║
║    - 报表生成                                             ║
║    - ClassTableData 交互测试                              ║
║    - 文件下载                                             ║
╚══════════════════════════════════════════════════════════╝
    """)

    app.run(host=args.host, port=args.port, debug=args.debug)
