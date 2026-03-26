"""FineReport Builder Web 服务

提供 Web 界面进行报表构建、Excel 转换、ClassTableData 测试等操作。
"""
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys_path = os.sys.path
sys_path.insert(0, str(PROJECT_ROOT))

from parsers.cpt_parser import CPTParser
from parsers.class_table_data import ClassTableDataParser
from parsers.excel_parser import ExcelParser

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# 配置
UPLOAD_FOLDER = PROJECT_ROOT / 'uploads'
OUTPUT_FOLDER = PROJECT_ROOT / 'outputs'
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
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


@app.route('/excel-convert')
def excel_convert_page():
    """Excel 转换页面"""
    return render_template('excel_convert.html')

@app.route('/excel-convert-v2')
def excel_convert_v2_page():
    """Excel 转换页面 V2"""
    return render_template('excel_convert_v2.html')


@app.route('/class-test')
def class_test_page():
    """ClassTableData 测试页面"""
    return render_template('class_test.html')


# ============ API 接口 ============

@app.route('/api/analyze/cpt', methods=['POST'])
def analyze_cpt():
    """分析 .cpt 文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.cpt'):
        return jsonify({'error': '请上传 .cpt 文件'}), 400
    
    # 保存上传文件
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = UPLOAD_FOLDER / filename
    file.save(filepath)
    
    try:
        # 解析 CPT
        parser = CPTParser()
        structure = parser.parse(str(filepath))
        summary = parser.to_summary(structure)
        
        # 解析 ClassTableData
        class_parser = ClassTableDataParser()
        class_definitions = class_parser.parse_from_cpt(str(filepath))
        
        result = {
            'success': True,
            'filename': file.filename,
            'summary': summary,
            'class_table_data': [
                {
                    'name': d.name,
                    'class_name': d.class_name,
                    'parameters': [
                        {
                            'name': p.name,
                            'default_value': p.default_value,
                            'type': p.infer_type()
                        }
                        for p in d.parameters
                    ]
                }
                for d in class_definitions
            ],
            'raw_structure': {
                'title': structure.title,
                'table_data_count': len(structure.table_data_list),
                'widget_controls_count': len(structure.widget_controls),
                'cell_elements_count': len(structure.cell_elements),
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/excel', methods=['POST'])
def analyze_excel():
    """分析 Excel 文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': '请上传 Excel 文件 (.xlsx/.xls)'}), 400
    
    # 保存上传文件
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = UPLOAD_FOLDER / filename
    file.save(filepath)
    
    try:
        # 解析 Excel
        parser = ExcelParser()
        structure = parser.parse(str(filepath))
        summary = parser.to_summary(structure)
        
        # 获取第一个 sheet 的单元格预览
        preview_data = []
        if structure.sheets:
            sheet = structure.sheets[0]
            cells_by_pos = {(c.column, c.row): c for c in sheet.cells}
            
            for row in range(min(sheet.max_row + 1, 20)):  # 最多预览 20 行
                row_data = []
                for col in range(min(sheet.max_column + 1, 20)):  # 最多预览 20 列
                    cell = cells_by_pos.get((col, row))
                    row_data.append(str(cell.value) if cell and cell.value is not None else '')
                preview_data.append(row_data)
        
        result = {
            'success': True,
            'filename': file.filename,
            'summary': summary,
            'preview': {
                'sheet_name': structure.sheets[0].name if structure.sheets else '',
                'max_row': structure.sheets[0].max_row if structure.sheets else 0,
                'max_column': structure.sheets[0].max_column if structure.sheets else 0,
                'data': preview_data
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/convert/excel-to-cpt', methods=['POST'])
def convert_excel_to_cpt():
    """将 Excel 转换为 .cpt"""
    data = request.json
    
    filename = data.get('filename')
    sheet_index = data.get('sheet_index', 0)
    ds_name = data.get('ds_name', 'data_source')
    database = data.get('database', 'default_db')
    
    # 查找上传的文件
    excel_files = list(UPLOAD_FOLDER.glob(f'*{filename}'))
    if not excel_files:
        return jsonify({'error': '找不到上传的文件'}), 400
    
    filepath = excel_files[-1]  # 取最新的
    
    try:
        parser = ExcelParser()
        structure = parser.parse(str(filepath))
        
        if sheet_index >= len(structure.sheets):
            return jsonify({'error': f'Sheet 索引 {sheet_index} 超出范围'}), 400
        
        sheet = structure.sheets[sheet_index]
        cells = parser.to_cpt_cells(sheet)
        styles = parser.to_cpt_styles(sheet.styles)
        
        # 生成 .cpt 文件内容（简化版）
        cpt_content = generate_cpt_xml(sheet.name, cells, styles, ds_name, database)
        
        # 保存输出文件
        output_filename = filepath.stem + '.cpt'
        output_path = OUTPUT_FOLDER / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cpt_content)
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'stats': {
                'cells': len(cells),
                'styles': len(styles),
                'rows': sheet.max_row + 1,
                'columns': sheet.max_column + 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/class-test/generate', methods=['POST'])
def generate_class_test():
    """生成 ClassTableData 测试页面"""
    data = request.json
    filename = data.get('filename')
    api_endpoint = data.get('api_endpoint', '')
    
    # 查找上传的文件
    cpt_files = list(UPLOAD_FOLDER.glob(f'*{filename}'))
    if not cpt_files:
        return jsonify({'error': '找不到上传的文件'}), 400
    
    filepath = cpt_files[-1]
    
    try:
        parser = ClassTableDataParser()
        definitions = parser.parse_from_cpt(str(filepath))
        
        if not definitions:
            return jsonify({'error': '未找到 ClassTableData 数据集'}), 400
        
        # 生成交互式 HTML
        html = parser.to_browser_html(definitions, api_endpoint)
        
        # 保存输出文件
        output_filename = filepath.stem + '_test.html'
        output_path = OUTPUT_FOLDER / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'view_url': f'/api/view/{output_filename}',
            'download_url': f'/api/download/{output_filename}',
            'data_sources': [
                {'name': d.name, 'class_name': d.class_name}
                for d in definitions
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    """列出已上传和输出的文件"""
    uploads = [{'name': f.name, 'size': f.stat().st_size, 'time': datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
               for f in UPLOAD_FOLDER.iterdir() if f.is_file()]
    
    outputs = [{'name': f.name, 'size': f.stat().st_size, 'time': datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
               for f in OUTPUT_FOLDER.iterdir() if f.is_file()]
    
    return jsonify({
        'uploads': sorted(uploads, key=lambda x: x['time'], reverse=True),
        'outputs': sorted(outputs, key=lambda x: x['time'], reverse=True)
    })


# ============ 辅助函数 ============

def generate_cpt_xml(title, cells, styles, ds_name, database):
    """生成 .cpt XML 内容（简化版）"""
    xml_parts = ['''<?xml version="1.0" encoding="UTF-8"?>
<WorkBook xmlVersion="20170720" releaseVersion="9.0.0">
<Report name="''' + title + '''" class="com.fr.report.worksheet.WorkSheet">
<TableDataMap>
    <TableData name="''' + ds_name + '''" class="com.fr.data.impl.DBTableData">
        <Connection class="com.fr.data.impl.NameDatabaseConnection">
            <DatabaseName><![CDATA[''' + database + ''']]></DatabaseName>
        </Connection>
        <Query><![CDATA[SELECT * FROM table_name]]></Query>
    </TableData>
</TableDataMap>
<CellElementList>
''']
    
    for cell in cells[:1000]:  # 限制最多 1000 个单元格
        xml_parts.append(f'''    <C c="{cell['column']}" r="{cell['row']}">
        <O><![CDATA[{cell['value']}]]></O>
    </C>
''')
    
    xml_parts.append('''</CellElementList>
</Report>
</WorkBook>''')
    
    return ''.join(xml_parts)


# ============ V2 API ============

@app.route('/api/v2/generate', methods=['POST'])
def generate_report_v2():
    """V2 报表生成接口"""
    data = request.json
    
    try:
        # 解析配置
        datasource = data.get('datasource', {})
        column_mapping = data.get('column_mapping', {})
        filter_components = data.get('filter_components', [])
        report_info = data.get('report', {})
        
        # 生成 CPT 配置
        cpt_config = {
            'title': report_info.get('title', '新建报表'),
            'sheet_name': report_info.get('sheet_name', 'Sheet1'),
            'data_sources': [],
            'filter_controls': [],
            'cells': []
        }
        
        # 数据源配置
        if datasource.get('type') == 'database':
            cpt_config['data_sources'].append({
                'name': datasource.get('name', 'main_data'),
                'type': 'DBTableData',
                'database': datasource.get('database', ''),
                'sql': datasource.get('sql', ''),
                'parameters': extract_params_from_sql(datasource.get('sql', ''))
            })
        elif datasource.get('type') == 'class':
            cpt_config['data_sources'].append({
                'name': datasource.get('name', 'main_data'),
                'type': 'ClassTableData',
                'class_name': datasource.get('class_name', ''),
                'return_fields': datasource.get('return_fields', []),
                'parameters': list(datasource.get('parameter_template', {}).keys())
            })
        
        # 筛选组件配置
        for i, comp in enumerate(filter_components):
            cpt_config['filter_controls'].append({
                'name': comp.get('code', f'param_{i}'),
                'label': comp.get('label', ''),
                'type': comp.get('type', 'TextEditor'),
                'default': comp.get('default_value', ''),
                'x': 100 + (i % 5) * 220,
                'y': 10 + (i // 5) * 50
            })
        
        # 单元格配置（从列映射生成）
        row = 0
        for col_letter, field_name in column_mapping.items():
            col_num = ord(col_letter.upper()) - ord('A')
            cpt_config['cells'].append({
                'column': col_num,
                'row': row,
                'value': field_name,
                'style_index': 0
            })
        
        # 生成 CPT 文件
        from parsers.cpt_generator import CPTGenerator
        generator = CPTGenerator()
        cpt_content = generator.generate(cpt_config)
        
        # 保存文件
        output_filename = f"{report_info.get('title', 'report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
        output_path = OUTPUT_FOLDER / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cpt_content)
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'config': cpt_config
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_params_from_sql(sql):
    """从 SQL 中提取参数名"""
    import re
    params = re.findall(r'\$\{(\w+)\}', sql)
    return [{'name': p, 'default': ''} for p in params]


# ============ 启动入口 ============

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FineReport Builder Web 服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         FineReport Builder Web 服务                       ║
╠══════════════════════════════════════════════════════════╣
║  地址: http://{args.host}:{args.port}                       ║
║  功能:                                                    ║
║    - CPT 文件分析                                         ║
║    - Excel 转 CPT                                         ║
║    - ClassTableData 交互测试                              ║
║    - 文件下载                                             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)