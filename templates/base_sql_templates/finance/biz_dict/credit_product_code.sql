-- 增信方式 — 业务字典
-- 对应 dict_code: finance_loan_product
-- 用途: 融资品种/增信方式下拉选择
-- 返回字段: dict_key, dict_value, 及其他业务扩展列
-- 变量: ${tenant_param} — 租户参数名（默认 fine_username9）
SELECT *
FROM sys_dict_biz
WHERE tenant_id = '${tenant_param}'
  AND is_deleted = 0
  AND status = 1
  AND code = 'finance_loan_product'
