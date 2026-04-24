-- 组织架构树 — 底层数据源
-- 用途: 查询组织机构列表，用于 Tree1 递归树
-- 变量: ${fine_username9}, ${orgStructure}, ${structureVersion}
SELECT so.`code`, concat(so.id, '') as id, concat(so.`code`, '-', so.`name`) as name, so.parent_id
FROM sys_organization so
${if(len(orgStructure)=0,"",if(structureVersion=1,
" INNER JOIN u_sys_organization_relation usor on usor.org_id = so.id and usor.is_deleted=0 and usor.tenant_id = ( '"+ fine_username9 +"') and usor.status = 1 INNER JOIN u_sys_organization_structure usos on usos.is_deleted = 0 and usos.tenant_id = ( '"+ fine_username9 +"') and usos.id =usor.structure_id and usor.structure_id =( '"+ orgStructure +"')",
" INNER JOIN u_sys_organization_relation usor on usor.org_id = so.id and usor.is_deleted=0 and usor.tenant_id = ( '"+ fine_username9 +"') and usor.status = 1 INNER JOIN u_sys_organization_structure usos on usos.is_deleted = 0 and usos.tenant_id = ( '"+ fine_username9 +"') and usos.id =usor.structure_id and usor.structure_id =( '"+ orgStructure +"')"))}
WHERE so.tenant_id = '${fine_username9}' AND so.is_deleted = 0 and so.status = 1
