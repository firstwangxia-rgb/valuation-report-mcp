# 资产评估报告智能撰写助手 MCP

[![CI](https://github.com/firstwangxia-rgb/valuation-report-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/firstwangxia-rgb/valuation-report-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

一个本地优先的 Model Context Protocol（MCP）服务器，用于检索资产评估知识库、生成企业价值评估报告 Markdown 初稿、执行规则型合规检查，并把已核验的公开公司资料写回本地知识库。

> [!IMPORTANT]
> 本项目只提供辅助检索、起草和检查能力，不构成正式资产评估意见、投资建议或法律意见。资产评估师仍须完成业务承接、现场调查、权属核验、评估测算、底稿复核、签字盖章并承担专业及法律责任。

## 功能

| MCP 工具 | 类型 | 作用 |
|---|---|---|
| `list_knowledge_base` | 只读 | 统计准则、案例、评估说明和公司档案 |
| `search_knowledge_base` | 只读 | 检索 Markdown、TXT、PDF、DOCX，并返回来源文件和片段 |
| `prepare_web_research` | 只读 | 生成联网调研问题、检索词和优先来源；不自行联网 |
| `draft_valuation_report` | 写入 | 根据已核验资料生成带来源的 Markdown 报告初稿 |
| `check_report_compliance` | 只读 | 检查必要章节、评估方法、URL 来源和使用限制声明 |
| `update_company_knowledge` | 写入 | 将带 URL 的公司新信息写入按日期命名的本地档案 |

此外提供：

- `valuation://instructions`：完整工作流和专业边界；
- `valuation://report-template`：标准报告章节模板；
- `full_valuation_workflow`：供 MCP 客户端调用的完整工作流提示词。

## 安全与隐私设计

- 默认仅通过本地 STDIO 运行，不开放网络端口；
- 所有读取和写入限定在 `VALUATION_MCP_WORKSPACE_ROOT` 内；
- 拒绝绝对输出路径、路径穿越和符号链接写入；
- 不执行知识库文件中的命令，也不把文件内容当成系统指令；
- 限制单文件大小、提取字符数和返回结果数；
- 仓库的 `.gitignore` 默认排除真实知识库、公司档案和生成报告。

## 环境要求

- Python 3.10 或更高版本；
- 支持 MCP 的客户端，例如 Codex CLI、Codex 桌面端或其他兼容客户端；
- 如需联网补充资料，由 MCP 宿主提供联网能力。本服务器本身不访问互联网，也不需要第三方搜索 API 密钥。

## 安装

```powershell
git clone https://github.com/firstwangxia-rgb/valuation-report-mcp.git
cd valuation-report-mcp
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Linux 或 macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## 准备本地工作区

建议把运行数据与 Git 仓库分开。例如：

```text
D:\valuation-workspace\
├── knowledge-base\
│   ├── 准则\
│   ├── 评估报告\
│   ├── 评估说明\
│   └── 公司档案\
└── reports\
```

支持检索 `.md`、`.txt`、`.pdf` 和 `.docx`。请确认放入本地知识库的准则版本现行有效，并确认你有权使用历史报告和教材。不要把受版权、保密或客户约束的文件提交到公开仓库。

## 在 Codex 中配置

将下列路径替换为本机的实际绝对路径：

```powershell
codex mcp add valuation-report --env VALUATION_MCP_WORKSPACE_ROOT=D:\valuation-workspace -- D:\code\valuation-report-mcp\.venv\Scripts\valuation-report-mcp.exe
codex mcp list
```

也可以参考 [`examples/codex-config.toml`](examples/codex-config.toml)，把配置加入项目级 `.codex/config.toml` 或用户级 Codex 配置。

## 使用示例

在 MCP 客户端中输入：

```text
请为“XX公司”生成企业价值评估报告初稿。先检索本地知识库；资料不足时列出联网调研计划并核验公开来源；随后起草报告、执行合规检查，最后把已核验的新资料更新到公司档案。不要虚构数据，所有关键数据注明 URL 和日期。
```

推荐执行顺序：

```text
本地盘点与检索
  -> 必要时由宿主联网核验
  -> 整理结构化资料
  -> 生成 Markdown 初稿
  -> 合规自检
  -> 人工专业复核
  -> 更新已核验的公开资料
```

写入工具要求显式传入结构化数据。示例输入见 [`examples/company-profile.json`](examples/company-profile.json)。

## 开发与测试

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest
```

测试包含路径边界、知识检索、报告生成、知识更新、合规检查和 MCP 客户端调用。

## 项目结构

```text
valuation-report-mcp/
├── src/valuation_report_mcp/   # MCP 服务与文件处理逻辑
├── tests/                      # 单元测试和协议测试
├── examples/                   # Codex 配置及结构化输入示例
├── knowledge-base/             # 仅保留目录骨架，不包含私有资料
├── reports/                    # 本地生成结果，默认不纳入 Git
├── .github/workflows/ci.yml    # GitHub Actions
├── pyproject.toml
└── LICENSE
```

## 发布前清单

1. 运行 `ruff check .` 与 `pytest`；
2. 用 `git status --short` 和 `git check-ignore` 确认真实知识库与报告未被纳入；
3. 根据资料权属决定是否需要额外的 `NOTICE`；
4. 创建 GitHub 仓库后提交并推送。

## 当前限制

- 合规检查是可解释的文本规则检查，不是法律或专业判断；
- PDF 仅检索可提取的文字层，不包含 OCR；
- DOCX 检索段落和表格文字，不解析批注、修订或嵌入附件；
- 报告模板不会计算企业价值，评估参数和结论必须由专业人员提供并复核；
- 联网调研由宿主执行，服务器只返回调研计划，避免内置搜索供应商和密钥。

## 参与贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [SECURITY.md](SECURITY.md)。提交示例或测试数据时，只能使用自有、已授权或明确可公开的内容。

## 许可证

代码采用 [MIT License](LICENSE)。知识库中的准则、教材、历史报告和公司资料不因本代码开源而自动获得相同许可。
