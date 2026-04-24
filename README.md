# FineReport Builder — Claude Code Skills for 帆软报表开发

将帆软报表开发经验沉淀为可复用的 **Claude Code Skills**，复制到任意项目即可直接使用。

## 使用方式

**下载项目到本地 → 在该项目下打开 Claude Code → 直接对话开发**

无需安装依赖，无需启动服务。Claude Code 会自动加载 `.claude/skills/` 中的技能定义。

```bash
# 1. 下载项目
git clone https://github.com/shangguanyongsheng/fineReport-builder.git
cd fineReport-builder

# 2. 复制 skills 到你的业务项目（可选）
cp -r .claude/skills/ 你的项目/.claude/

# 3. 在 Claude Code 中直接对话，描述报表需求即可
```

## 内置 Skills

| Skill | 类型 | 用途 |
|-------|------|------|
| `/cpt-knowledge` | reference | 加载 CPT 知识库（XML 结构、控件类型、样式系统） |
| `/cpt-create` | tool | 从零创建全新的 .cpt 报表文件 |
| `/cpt-modify` | tool | 基于现有 .cpt 模板增删筛选组件、数据列、参数 |
| `/cpt-validate` | tool | 验证 .cpt 文件是否符合帆软规范 |

### 创建新报表流程

```
/cpt-knowledge          ← 加载知识库
描述你的需求              ← 数据源、筛选条件、展示列
/cpt-create             ← 生成 .cpt 文件
/cpt-validate           ← 验证规范
```

### 修改现有报表流程

```
/cpt-knowledge          ← 加载知识库
描述修改内容              ← 新增/删除什么组件或列
/cpt-modify             ← 修改 .cpt 文件
/cpt-validate           ← 验证规范
```

## 项目结构

| 目录 | 定位 | 说明 |
|------|------|------|
| `.claude/skills/` | **核心交付物** | 可复制到其他项目的 Skills 包 |
| `cpt_tools/` | 命令行工具 | 生成、校验，可独立使用或被 Skills 调用 |
| `parsers/` | 解析器库 | CPT 生成/解析、ClassTableData 支持，供 tools 调用 |
| `templates/` | 知识文档 | CPT XML 模板结构详解，Skill 的知识引用 |
| `web/` | 测试工具 | 验证 Skills 生成的 CPT 是否正确，非交付物 |

## 命令行工具（可选）

不通过对话，直接通过命令行生成和校验：

```bash
# 通过 JSON 配置生成报表
python cpt_tools/generate.py --config config.json --output report.cpt

# 通过 stdin 传入配置
echo '{"title":"测试","data_sources":[...],"cells":[...]}' | \
  python cpt_tools/generate.py --stdin --output report.cpt

# 修改现有报表
python cpt_tools/generate.py --modify report.cpt \
    --add-filters '[{"label":"区域","code":"region","type":"ComboBox"}]' \
    --add-columns '[{"header":"区域","field":"region"}]' \
    --output modified.cpt

# 校验报表
python cpt_tools/validate.py report.cpt
```

## 本地代码引用（可选）

```python
from parsers.cpt_generator import CPTGenerator
from cpt_tools.validate import validate_cpt

generator = CPTGenerator()
cpt_content = generator.generate(config_dict)
result = validate_cpt("report.cpt")
```

## 核心约束

- **数据源参数只能多不能少**：筛选组件必须覆盖所有空值参数
- **ClassTableData 必须有 `<Parameters>` 节点**
- **`<O>` 标签必须用 CDATA 格式**：`<O><![CDATA[value]]></O>`
- **样式索引必须在 StyleList 范围内**
- **筛选组件布局**：每行 5 对（Label 89px + Input 135px），间距 4px，行间距 8px

## License

MIT
