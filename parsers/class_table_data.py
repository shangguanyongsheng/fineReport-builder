"""ClassTableData 解析器和交互模块

解析帆软 ClassTableData 数据集，支持：
1. 提取类名、参数定义
2. 生成交互式参数表单
3. 构建测试请求
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import re


@dataclass
class ClassParameter:
    """Class 数据集参数"""
    name: str
    default_value: str = ""
    description: str = ""  # 从参数名推断的描述
    param_type: str = "string"  # string, number, date, array, object
    
    def infer_type(self) -> str:
        """从参数名推断类型"""
        name_lower = self.name.lower()
        
        # 日期类型
        if any(kw in name_lower for kw in ['date', 'time', '日期', '时间']):
            return "date"
        
        # 数字类型
        if any(kw in name_lower for kw in ['id', 'code', 'amount', '数量', '金额', 'count']):
            return "number"
        
        # 数组/列表类型
        if any(kw in name_lower for kw in ['ids', 'codes', 'list', 'array', 'dimensions', 'indexinfo']):
            return "array"
        
        # JSON 对象
        if any(kw in name_lower for kw in ['info', 'config', 'mapping', 'condition']):
            return "object"
        
        # 布尔类型
        if any(kw in name_lower for kw in ['is', 'has', 'enable', 'boolean']):
            return "boolean"
        
        return "string"


@dataclass
class ClassTableDataDefinition:
    """ClassTableData 数据集定义"""
    name: str
    class_name: str
    parameters: List[ClassParameter] = field(default_factory=list)
    raw_xml: str = ""
    
    def to_interactive_form(self) -> Dict[str, Any]:
        """生成交互式表单配置"""
        form_fields = []
        
        for param in self.parameters:
            field_config = {
                "name": param.name,
                "label": self._infer_label(param.name),
                "type": param.infer_type(),
                "default": param.default_value,
                "required": self._is_required(param.name)
            }
            
            # 添加特殊配置
            if field_config["type"] == "date":
                field_config["format"] = "YYYY-MM-DD"
            elif field_config["type"] == "array":
                field_config["itemType"] = "string"
            
            form_fields.append(field_config)
        
        return {
            "dataSourceName": self.name,
            "className": self.class_name,
            "fields": form_fields
        }
    
    def _infer_label(self, param_name: str) -> str:
        """从参数名推断标签"""
        # 常见参数名映射
        label_map = {
            "orgStructure": "组织架构",
            "orgId": "被授信人",
            "convertCurrencyCode": "折算币种",
            "fine_username9": "租户ID",
            "fr_usercode": "用户ID",
            "widgetId": "组件ID",
            "startStartDate": "开始日期-开始",
            "endStartDate": "开始日期-结束",
            "startEndDate": "结束日期-开始",
            "endEndDate": "结束日期-结束",
            "indexInfo": "指标信息",
            "dimensions": "维度",
            "condition": "条件",
            "fieldMapping": "字段映射",
            "triggerRequest": "触发请求",
            "orgTag": "组织标签",
            "contain": "是否包含下级",
            "financeBankCode": "银行授信机构",
            "financeBankName": "其他授信机构",
            "isCirculate": "额度循环",
            "creditProtocolType": "协议类型",
            "creditProductCode": "融资品种",
            "bizType": "批文/授信",
            "financeTypeCode": "授信类型",
        }
        
        return label_map.get(param_name, param_name)
    
    def _is_required(self, param_name: str) -> bool:
        """判断参数是否必填"""
        required_params = [
            "widgetId", "fine_username9", "tenant_id", "user_id"
        ]
        return param_name in required_params


class ClassTableDataParser:
    """ClassTableData 解析器"""
    
    def parse_from_cpt(self, file_path: str) -> List[ClassTableDataDefinition]:
        """从 .cpt 文件解析所有 ClassTableData"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        root = ET.fromstring(content)
        return self.parse_from_root(root)
    
    def parse_from_root(self, root: ET.Element) -> List[ClassTableDataDefinition]:
        """从 XML 根节点解析"""
        definitions = []
        table_data_map = root.find('TableDataMap')
        
        if table_data_map is None:
            return definitions
        
        for table_data_elem in table_data_map.findall('TableData'):
            class_attr = table_data_elem.get('class', '')
            
            # 只处理 ClassTableData
            if 'ClassTableData' not in class_attr:
                continue
            
            definition = ClassTableDataDefinition(
                name=table_data_elem.get('name', ''),
                class_name=""
            )
            
            # 解析参数
            params_elem = table_data_elem.find('Parameters')
            if params_elem is not None:
                for param_elem in params_elem.findall('Parameter'):
                    name_elem = param_elem.find('Attributes')
                    if name_elem is not None:
                        param = ClassParameter(
                            name=name_elem.get('name', '')
                        )
                        
                        # 解析默认值
                        default_elem = param_elem.find('O')
                        if default_elem is not None and default_elem.text:
                            param.default_value = default_elem.text.strip()
                            # 从默认值推断类型
                            if param.default_value.startswith('['):
                                param.param_type = "array"
                            elif param.default_value.startswith('{'):
                                param.param_type = "object"
                        
                        definition.parameters.append(param)
            
            # 解析类名
            class_elem = table_data_elem.find('ClassTableDataAttr')
            if class_elem is not None:
                definition.class_name = class_elem.get('className', '')
            
            # 保存原始 XML
            definition.raw_xml = ET.tostring(table_data_elem, encoding='unicode')
            
            definitions.append(definition)
        
        return definitions
    
    def generate_test_request(self, definition: ClassTableDataDefinition, 
                               param_values: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试请求体"""
        request_body = {
            "widgetId": param_values.get("widgetId", 0),
            "tenantId": param_values.get("fine_username9", param_values.get("tenantId", "")),
            "userId": param_values.get("fr_usercode", param_values.get("userId", 0)),
        }
        
        # 添加可选参数
        for param in definition.parameters:
            if param.name in param_values and param_values[param.name]:
                # 处理字段映射
                field_mapping = param_values.get("fieldMapping", {})
                mapped_name = field_mapping.get(param.name, param.name)
                
                value = param_values[param.name]
                
                # 处理数组参数
                if param.param_type == "array" and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        value = value.split(',')
                
                request_body[mapped_name] = value
        
        return request_body
    
    def to_browser_html(self, definitions: List[ClassTableDataDefinition], 
                        api_endpoint: str = "") -> str:
        """生成浏览器交互界面 HTML"""
        html_parts = ['''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClassTableData 交互测试</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card-header { padding: 16px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .card-header h3 { margin: 0; color: #333; }
        .card-body { padding: 20px; }
        .class-name { font-family: monospace; background: #f0f0f0; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; margin-bottom: 4px; font-weight: 500; color: #555; font-size: 13px; }
        .form-group input, .form-group select, .form-group textarea { 
            width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;
        }
        .form-group textarea { min-height: 80px; font-family: monospace; }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus { 
            outline: none; border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); 
        }
        .required::after { content: " *"; color: red; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #1890ff; color: white; }
        .btn-primary:hover { background: #40a9ff; }
        .btn-secondary { background: #f0f0f0; color: #333; }
        .btn-secondary:hover { background: #d9d9d9; }
        .result-section { margin-top: 20px; }
        .result-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
        .tab-btn { padding: 8px 16px; background: #f0f0f0; border: none; border-radius: 4px; cursor: pointer; }
        .tab-btn.active { background: #1890ff; color: white; }
        .result-content { background: #fafafa; border: 1px solid #eee; border-radius: 4px; padding: 16px; max-height: 500px; overflow: auto; }
        pre { margin: 0; white-space: pre-wrap; word-break: break-all; font-size: 12px; }
        .json-view { font-family: monospace; }
        .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
        .status-success { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .api-config { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
        .api-config input { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 ClassTableData 交互测试工具</h1>
        
        <div class="card">
            <div class="card-header">
                <span>API 配置</span>
            </div>
            <div class="card-body">
                <div class="api-config">
                    <label>接口地址:</label>
                    <input type="text" id="apiEndpoint" placeholder="http://localhost:8080/data/dashboard/load-data" 
                           value="''' + api_endpoint + '''">
                    <button class="btn btn-secondary" onclick="saveApiConfig()">保存</button>
                </div>
            </div>
        </div>
''']
        
        # 为每个 ClassTableData 生成表单
        for idx, definition in enumerate(definitions):
            form_config = definition.to_interactive_form()
            
            html_parts.append(f'''
        <div class="card" id="ds-{idx}">
            <div class="card-header">
                <h3>{definition.name}</h3>
                <span class="class-name">{definition.class_name}</span>
            </div>
            <div class="card-body">
                <form id="form-{idx}" class="form-grid" onsubmit="return submitForm(event, {idx})">
''')
            
            # 生成表单字段
            for field in form_config["fields"]:
                required_class = "required" if field.get("required") else ""
                field_type = "text"
                if field["type"] == "date":
                    field_type = "date"
                elif field["type"] == "number":
                    field_type = "number"
                
                if field["type"] in ["array", "object"]:
                    html_parts.append(f'''
                    <div class="form-group">
                        <label class="{required_class}">{field["label"]}</label>
                        <textarea name="{field["name"]}" placeholder='[{field["type"] == "array" and "\"value\"" or "{\"key\": \"value\"}"}]'>{field.get("default", "")}</textarea>
                    </div>
''')
                else:
                    html_parts.append(f'''
                    <div class="form-group">
                        <label class="{required_class}">{field["label"]}</label>
                        <input type="{field_type}" name="{field["name"]}" value="{field.get("default", "")}" placeholder="{field["label"]}">
                    </div>
''')
            
            html_parts.append(f'''
                    <div style="grid-column: 1 / -1; display: flex; gap: 12px; margin-top: 12px;">
                        <button type="submit" class="btn btn-primary">🚀 发送请求</button>
                        <button type="button" class="btn btn-secondary" onclick="resetForm({idx})">🔄 重置</button>
                    </div>
                </form>
                
                <div class="result-section" id="result-{idx}" style="display: none;">
                    <div class="result-tabs">
                        <button class="tab-btn active" onclick="showTab({idx}, 'response')">响应体</button>
                        <button class="tab-btn" onclick="showTab({idx}, 'request')">请求体</button>
                    </div>
                    <div class="result-content">
                        <div id="response-{idx}" class="json-view">
                            <pre></pre>
                        </div>
                        <div id="request-{idx}" class="json-view" style="display: none;">
                            <pre></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
''')
        
        # JavaScript 部分
        html_parts.append('''
    </div>
    
    <script>
        // 数据源定义
        const dataSources = ''' + json.dumps([d.to_interactive_form() for d in definitions], ensure_ascii=False, indent=2) + ''';
        
        // 获取 API 地址
        function getApiEndpoint() {
            return document.getElementById('apiEndpoint').value || 'http://localhost:8080/data/dashboard/load-data';
        }
        
        function saveApiConfig() {
            localStorage.setItem('apiEndpoint', getApiEndpoint());
            alert('API 配置已保存');
        }
        
        // 页面加载时恢复配置
        window.onload = function() {
            const saved = localStorage.getItem('apiEndpoint');
            if (saved) {
                document.getElementById('apiEndpoint').value = saved;
            }
        };
        
        // 提交表单
        async function submitForm(event, dsIndex) {
            event.preventDefault();
            
            const form = document.getElementById('form-' + dsIndex);
            const formData = new FormData(form);
            const params = {};
            
            for (let [key, value] of formData.entries()) {
                if (value) {
                    // 尝试解析 JSON
                    if (value.startsWith('[') || value.startsWith('{')) {
                        try {
                            params[key] = JSON.parse(value);
                        } catch {
                            params[key] = value;
                        }
                    } else {
                        params[key] = value;
                    }
                }
            }
            
            // 构建请求体
            const requestBody = {
                widgetId: parseInt(params.widgetId) || dataSources[dsIndex].widgetId || 0,
                tenantId: params.tenantId || params.fine_username9 || '',
                userId: params.userId || params.fr_usercode || '',
                ...params
            };
            
            // 显示请求体
            document.getElementById('request-' + dsIndex).querySelector('pre').textContent = 
                JSON.stringify(requestBody, null, 2);
            
            // 发送请求
            const resultSection = document.getElementById('result-' + dsIndex);
            resultSection.style.display = 'block';
            
            const responseEl = document.getElementById('response-' + dsIndex).querySelector('pre');
            responseEl.textContent = '⏳ 请求中...';
            
            try {
                const response = await fetch(getApiEndpoint(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                const data = await response.json();
                responseEl.textContent = JSON.stringify(data, null, 2);
                
            } catch (error) {
                responseEl.textContent = '❌ 请求失败: ' + error.message;
            }
            
            return false;
        }
        
        // 重置表单
        function resetForm(dsIndex) {
            document.getElementById('form-' + dsIndex).reset();
            document.getElementById('result-' + dsIndex).style.display = 'none';
        }
        
        // 切换标签
        function showTab(dsIndex, tab) {
            const tabs = document.querySelectorAll('#ds-' + dsIndex + ' .tab-btn');
            tabs.forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('response-' + dsIndex).style.display = tab === 'response' ? 'block' : 'none';
            document.getElementById('request-' + dsIndex).style.display = tab === 'request' ? 'block' : 'none';
        }
    </script>
</body>
</html>
''')
        
        return ''.join(html_parts)


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python class_table_data.py <file.cpt>")
        sys.exit(1)
    
    parser = ClassTableDataParser()
    definitions = parser.parse_from_cpt(sys.argv[1])
    
    print(f"\n找到 {len(definitions)} 个 ClassTableData:\n")
    
    for d in definitions:
        print(f"📌 {d.name}")
        print(f"   类名: {d.class_name}")
        print(f"   参数: {[p.name for p in d.parameters]}")
        print()
    
    # 生成交互式 HTML
    html = parser.to_browser_html(definitions)
    output_path = sys.argv[1].replace('.cpt', '_interactive.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 交互式 HTML 已生成: {output_path}")