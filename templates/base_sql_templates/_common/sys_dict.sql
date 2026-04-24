-- 系统字典查询（无租户隔离）
-- 返回字段: id, code, dict_key, dict_value
-- 适用场景: 全局字典如币种(currency)等
-- 变量: ${dict_code} — 字典编码
select concat(id,'') as id, code, dict_key, dict_value
from sys_dict
where code = '${dict_code}'
  and is_deleted = 0
