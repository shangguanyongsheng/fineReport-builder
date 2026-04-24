"""SQL 数据源生成器

从 base_sql_templates 加载 SQL 模板，生成帆软 DBTableData / RecursionTableData XML 定义。

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

    # 方式4: 生成树数据源（底层 DBTableData + RecursionTableData 包装）
    sources = gen.generate_tree(
        tree_name="融资品种",
        base_data_source="creditProductCode",
        mark_field_index=0,
        parent_mark_field_index=2,
        mark_field_name="id",
        parent_mark_field_name="parent_id",
    )
    # sources = [db_ds_config, tree_ds_config]

    # 方式5: 从 YAML 配置加载树定义
    sources = gen.load_tree_template("finance/tree/credit_product_tree.yaml")

    # 生成 XML
    xml = gen.to_xml(ds)
    tree_xml = gen.tree_to_xml(tree_ds_config)
"""
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import xml.etree.ElementTree as ET
import yaml


# 模板根目录
TEMPLATES_DIR = Path(__file__).parent.parent / 'templates' / 'base_sql_templates'


class SqlDataSourceGenerator:
    """SQL 数据源 & 树数据源 XML 生成器"""

    DEFAULT_TENANT_PARAM = "fine_username9"

    def __init__(self):
        self.templates_dir = TEMPLATES_DIR

    # ─────────────────────────── 业务字典 ───────────────────────────

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
        """生成系统字典数据源配置（sys_dict 查询，无租户隔离）"""
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

    # ─────────────────────────── 原始 SQL ───────────────────────────

    def from_sql(
        self,
        name: str,
        sql: str,
        database: str = "cfs-report",
        parameters: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """直接从 SQL 字符串创建数据源配置"""
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
            template_path: 相对于 base_sql_templates 的路径
            database: 数据库名称
            variables: 模板变量，值会自动包装为 ${value} 帆软运行时变量
            parameters: 数据源参数列表
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

    # ─────────────────────────── 树数据源 ───────────────────────────

    def generate_tree(
        self,
        tree_name: str,
        base_data_source: str,
        mark_field_index: int,
        parent_mark_field_index: int,
        mark_field_name: str = "id",
        parent_mark_field_name: str = "parent_id",
    ) -> Tuple[None, Dict[str, Any]]:
        """生成 RecursionTableData 树数据源配置

        Args:
            tree_name: 树数据源名称（如 "融资品种", "Tree1"）
            base_data_source: 底层 DBTableData 的名称
            mark_field_index: 节点 ID 列索引（从 0 开始）
            parent_mark_field_index: 父节点 ID 列索引
            mark_field_name: 节点 ID 字段名
            parent_mark_field_name: 父节点 ID 字段名

        Returns:
            (None, tree_ds_config) — 树节点配置（底层数据源需单独生成）
        """
        tree_ds = {
            "name": tree_name,
            "type": "RecursionTableData",
            "base_data_source": base_data_source,
            "mark_field_index": mark_field_index,
            "parent_mark_field_index": parent_mark_field_index,
            "mark_field_name": mark_field_name,
            "parent_mark_field_name": parent_mark_field_name,
        }
        return (None, tree_ds)

    def load_tree_template(
        self,
        template_path: str,
    ) -> Tuple[None, Dict[str, Any]]:
        """从 YAML 模板文件加载树配置

        Args:
            template_path: 相对于 base_sql_templates 的路径（如 finance/tree/credit_product_tree.yaml）

        Returns:
            (None, tree_ds_config)
        """
        full_path = self.templates_dir / template_path
        if not str(full_path).endswith(".yaml"):
            full_path = full_path.with_suffix(".yaml")
        if not full_path.exists():
            raise FileNotFoundError(f"树模板文件不存在: {full_path}")

        with open(full_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return self.generate_tree(
            tree_name=config["name"],
            base_data_source=config["base_data_source"],
            mark_field_index=config["mark_field_index"],
            parent_mark_field_index=config["parent_mark_field_index"],
            mark_field_name=config.get("mark_field_name", "id"),
            parent_mark_field_name=config.get("parent_mark_field_name", "parent_id"),
        )

    def generate_organization_tree(
        self,
        tree_name: str = "Tree1",
        tenant_param: str = DEFAULT_TENANT_PARAM,
        database: str = "cfs-report",
    ) -> List[Dict[str, Any]]:
        """生成完整的组织架构树数据源（3 个 DBTableData + 1 个 RecursionTableData）

        Returns:
            [orgStructure, structureVersion, organization, Tree1] 四个数据源配置
        """
        variables = {"fine_username9": tenant_param, "structureVersion": tenant_param, "orgStructure": tenant_param}

        org_structure = self.from_template_file(
            name="orgStructure",
            template_path="_common/tree/org_structure.sql",
            database=database,
            parameters=[
                {"name": tenant_param, "default": ""},
                {"name": "structureVersion", "default": ""},
            ],
        )

        structure_version = self.from_template_file(
            name="structureVersion",
            template_path="_common/tree/structure_version.sql",
            database=database,
        )

        organization = self.from_template_file(
            name="organization",
            template_path="_common/tree/organization.sql",
            database=database,
            parameters=[
                {"name": tenant_param, "default": ""},
                {"name": "orgStructure", "default": ""},
                {"name": "structureVersion", "default": ""},
            ],
        )

        _, tree1 = self.generate_tree(
            tree_name=tree_name,
            base_data_source="organization",
            mark_field_index=1,
            parent_mark_field_index=3,
            mark_field_name="id",
            parent_mark_field_name="parent_id",
        )

        return [org_structure, structure_version, organization, tree1]

    def generate_finance_dict_tree(
        self,
        dict_code: str = "finance_loan_product",
        tree_name: str = "融资品种",
        tenant_param: str = DEFAULT_TENANT_PARAM,
        database: str = "cfs-report",
    ) -> List[Dict[str, Any]]:
        """生成财务字典树数据源（DBTableData + RecursionTableData）

        Returns:
            [creditProductCode, 融资品种] 两个数据源配置
        """
        biz_dict = self.generate_biz_dict(
            name="creditProductCode",
            dict_code=dict_code,
            database=database,
            tenant_param=tenant_param,
        )

        _, tree = self.generate_tree(
            tree_name=tree_name,
            base_data_source="creditProductCode",
            mark_field_index=0,
            parent_mark_field_index=2,
            mark_field_name="id",
            parent_mark_field_name="parent_id",
        )

        return [biz_dict, tree]

    # ─────────────────────────── XML 生成 ───────────────────────────

    @staticmethod
    def to_xml(ds: Dict[str, Any]) -> ET.Element:
        """将 DBTableData 数据源配置转为 XML Element"""
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

    @staticmethod
    def tree_to_xml(ds: Dict[str, Any]) -> ET.Element:
        """将 RecursionTableData 树数据源配置转为 XML Element"""
        table_data = ET.Element("TableData")
        table_data.set("name", ds["name"])
        table_data.set("class", "com.fr.data.impl.RecursionTableData")

        # Desensitizations
        desens = ET.SubElement(table_data, "Desensitizations")
        desens.set("desensitizeOpen", "false")

        # markFields
        mf = ET.SubElement(table_data, "markFields")
        mf.text = f"<![CDATA[{ds['mark_field_index']}]]>"

        # parentmarkFields
        pmf = ET.SubElement(table_data, "parentmarkFields")
        pmf.text = f"<![CDATA[{ds['parent_mark_field_index']}]]>"

        # markFieldsName
        mfn = ET.SubElement(table_data, "markFieldsName")
        mfn.text = f"<![CDATA[{ds['mark_field_name']}]]>"

        # parentmarkFieldsName
        pmfn = ET.SubElement(table_data, "parentmarkFieldsName")
        pmfn.text = f"<![CDATA[{ds['parent_mark_field_name']}]]>"

        # originalTableDataName
        otn = ET.SubElement(table_data, "originalTableDataName")
        otn.text = f"<![CDATA[{ds['base_data_source']}]]>"

        return table_data
