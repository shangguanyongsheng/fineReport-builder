-- 业务字典查询（含租户隔离）
-- 返回字段: 所有列 (SELECT *)
-- 适用场景: 带租户隔离的业务字典
-- 变量:
--   ${dict_code}     — 字典编码
--   ${tenant_param}  — 租户参数名（默认 fine_username9）
SELECT *
FROM sys_dict_biz
WHERE tenant_id = '${tenant_param}'
  AND is_deleted = 0
  AND status = 1
  AND code = '${dict_code}'
