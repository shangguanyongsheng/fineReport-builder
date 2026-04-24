"""SQL 数据源生成器

从 base_sql_templates 加载 SQL 模板，生成帆软 DBTableData XML 定义。

用法：
    gen = SqlDataSourceGenerator()

    # 方式1: 使用通用业务字典模板
    ds = gen.generate_biz_dict(
        name="creditProductCode",
        dict_code="finance_loan_product",
        database="cfs-report",
        tenant_param="fine_username9"
    )

    # 方式2: 从文件加载模板并替换变量
    ds = gen.from_template_file(
        name="creditProductCode",
        template_path="finance/biz_dict/credit_product_code.sql",
        database="cfs-report",
        variables={"tenant_param": "fine_username9"}
    )

    # 方式3: 直接用 SQL
    ds = gen.from_sql(
        name="currency",
        sql="select concat(id,'') as id,code,dict_key,dict_value from sys_dict where code = 'currency' and is_deleted = 0",
        database="cfs-report"
    )

    # 生成 XML
    xml = gen.to_xml(ds)
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET


# 模板根目录
TEMPLATES_DIR = Path(__file__).parent.parent / 'templates' / 'base_sql_templates'


class SqlDataSourceGenerator:
    """SQL 数据源 XML 生成器"""

    DEFAULT_TENANT_PARAM = "fine_username9"

    def __init__(self):
        self.templates_dir = TEMPLATES_DIR

    def generate_biz_dict(
        self,
        name: str,
        dict_code: str,
        database: str = "cfs-report",
        tenant_param: str = DEFAULT_TENANT_PARAM,
        extra_params: Optional[List[Dict[str, str]]] = None,
        return_all: bool = True,
    ) -> Dict[str, Any]:
        """生成业务字典数据源配置（sys_dict_biz 查询）

        Args:
            name: 数据源名称（如 creditProductCode）
            dict_code: 业务字典编码（如 finance_loan_product）
            database: 数据库名称
            tenant_param: 租户参数名
            extra_params: 额外参数列表 [{"name": "xxx", "default": ""}]
            return_all: True=SELECT *  False=只返回 dict_key, dict_value

        Returns:
            数据源配置字典，可直接用于 cpt_generator
        """
        fields = "*" if return_all else "dict_key, dict_value"
        sql = (
            f"SELECT {fields} FROM sys_dict_biz "
            f"WHERE tenant_id = '${{{tenant_param}}}' AND is_deleted = 0 "
            f"AND status = 1 AND code = '{dict_code}'"
        )

        params = [{"name": tenant_param, "default": ""}]
        if extra_params:
            params.extend(extra_params)

        return {
            "name": name,
            "type": "DBTableData",
            "database": database,
            "parameters": params,
            "sql": sql,
        }

    def generate_sys_dict(
        self,
        name: str,
        dict_code: str,
        database: str = "cfs-report",
    ) -> Dict[str, Any]:
        """生成系统字典数据源配置（sys_dict 查询，无租户隔离）

        Args:
            name: 数据源名称
            dict_code: 字典编码
            database: 数据库名称

        Returns:
            数据源配置字典
        """
        sql = (
            f"select concat(id,'') as id,code,dict_key,dict_value "
            f"from sys_dict where code = '{dict_code}' and is_deleted = 0"
        )

        return {
            "name": name,
            "type": "DBTableData",
            "database": database,
            "parameters": [],
            "sql": sql,
        }

    def from_sql(
        self,
        name: str,
        sql: str,
        database: str = "cfs-report",
        parameters: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """直接从 SQL 字符串创建数据源配置

        Args:
            name: 数据源名称
            sql: SQL 查询语句
            database: 数据库名称
            parameters: 参数列表

        Returns:
            数据源配置字典
        """
        return {
            "name": name,
            "type": "DBTableData",
            "database": database,
            "parameters": parameters or [],
            "sql": sql,
        }

    def from_template_file(
        self,
        name: str,
        template_path: str,
        database: str = "cfs-report",
        variables: Optional[Dict[str, str]] = None,
        parameters: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """从模板文件加载 SQL 并生成数据源配置

        Args:
            name: 数据源名称
            template_path: 相对于 base_sql_templates 的路径（如 finance/biz_dict/credit_product_code.sql）
            database: 数据库名称
            variables: 模板变量（如 {"tenant_param": "fine_username9"}）
                       值会自动包装为 ${value} 帆软运行时变量
            parameters: 数据源参数列表

        Returns:
            数据源配置字典
        """
        full_path = self.templates_dir / template_path
        if not str(full_path).endswith(".sql"):
            full_path = full_path.with_suffix(".sql")
        if not full_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {full_path}")

        sql = full_path.read_text(encoding="utf-8")
        # 替换 ${var} 占位符 — 值自动包装为 ${value} 格式供帆软运行时解析
        if variables:
            for key, value in variables.items():
                sql = sql.replace(f"${{{key}}}", f"${{{value}}}")
        # 移除注释行（仅保留有效 SQL）
        sql_lines = [
            line for line in sql.split("\n")
            if not line.strip().startswith("--") and line.strip()
        ]
        sql = " ".join(line.strip() for line in sql_lines)

        return {
            "name": name,
            "type": "DBTableData",
            "database": database,
            "parameters": parameters or [],
            "sql": sql,
        }

    @staticmethod
    def to_xml(ds: Dict[str, Any]) -> ET.Element:
        """将数据源配置转为 XML Element

        Args:
            ds: 数据源配置字典

        Returns:
            XML Element
        """
        table_data = ET.Element("TableData")
        table_data.set("name", ds["name"])
        table_data.set("class", "com.fr.data.impl.DBTableData")

        # Desensitizations
        desens = ET.SubElement(table_data, "Desensitizations")
        desens.set("desensitizeOpen", "false")

        # Parameters
        params_elem = ET.SubElement(table_data, "Parameters")
        for p in ds.get("parameters", []):
            param = ET.SubElement(params_elem, "Parameter")
            attrs = ET.SubElement(param, "Attributes")
            attrs.set("name", p.get("name", ""))
            o = ET.SubElement(param, "O")
            o.text = f"<![CDATA[{p.get('default', '')}]]>"

        # Attributes
        attr = ET.SubElement(table_data, "Attributes")
        attr.set("maxMemRowCount", "-1")

        # Connection
        conn = ET.SubElement(table_data, "Connection")
        conn.set("class", "com.fr.data.impl.NameDatabaseConnection")
        dbname = ET.SubElement(conn, "DatabaseName")
        dbname.text = f"<![CDATA[{ds.get('database', '')}]]>"

        # Query
        query = ET.SubElement(table_data, "Query")
        query.text = f"<![CDATA[{ds.get('sql', '')}]]>"

        # PageQuery
        pq = ET.SubElement(table_data, "PageQuery")
        pq.text = "<![CDATA[]]>"

        return table_data
