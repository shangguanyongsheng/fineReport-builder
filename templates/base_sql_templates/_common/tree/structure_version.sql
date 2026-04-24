-- 组织架构版本字典
-- 用途: 查询 org_structure 字典值（版本下拉选项）
SELECT sd1.dict_key, sd1.dict_value
FROM sys_dict sd1
WHERE sd1.`code` = 'org_structure'
  AND sd1.is_deleted = 0 AND sd1.`status` = 1
