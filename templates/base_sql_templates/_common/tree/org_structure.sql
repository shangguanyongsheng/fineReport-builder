-- 组织架构版本列表
-- 用途: 查询租户可用的组织架构版本
-- 变量: ${fine_username9} — 租户参数, ${structureVersion} — 版本筛选参数
SELECT so.`version`, concat(so.id, '') as id
FROM u_sys_organization_structure so
WHERE so.tenant_id = '${fine_username9}' AND so.is_deleted = 0
${if(len(structureVersion)=0,"AND 1=2",if(structureVersion=1,"AND so.structure_type =( '"+ structureVersion +"')  and so.effective_date<=DATE_FORMAT(NOW(),'%Y-%m-%d') and so.expiry_date>=DATE_FORMAT(NOW(),'%Y-%m-%d')","AND so.structure_type =( '"+ structureVersion +"')"))}
