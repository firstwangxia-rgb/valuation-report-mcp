"""MCP server entry point for the valuation report assistant."""

from __future__ import annotations

from typing import Annotated

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .core import (
    WorkspaceConfig,
    list_knowledge,
    search_knowledge,
    write_company_knowledge,
)
from .core import (
    check_compliance as run_compliance_check,
)
from .core import (
    prepare_research_plan as build_research_plan,
)
from .core import (
    write_report as write_valuation_report,
)
from .schemas import (
    CompanyKnowledgeRequest,
    ComplianceResult,
    DraftReportRequest,
    KnowledgeInventory,
    ResearchPlan,
    SearchResponse,
    WriteResult,
)

SERVER_INSTRUCTIONS = """你是资产评估报告撰写助手。默认工作流：先调用
list_knowledge_base 和 search_knowledge_base 检索本地准则、案例与公司档案；资料不足时
调用 prepare_web_research 获得联网调研问题与检索词，并由宿主完成联网检索、保留 URL；
随后调用 draft_valuation_report 生成 Markdown 初稿，再调用 check_report_compliance 自检；
最后经用户确认后调用 update_company_knowledge 保存新增公开信息。不得虚构数据、准则条文、
评估参数或结论。工具输出仅是工作底稿，不能替代资产评估专业人员的核查、判断、签字和法律责任。
"""


mcp = MCPServer(
    "valuation-report-mcp",
    title="资产评估报告智能撰写助手",
    description="面向本地知识库的企业价值评估报告检索、起草、合规检查与知识更新工具。",
    instructions=SERVER_INSTRUCTIONS,
    version=__version__,
)


def _config() -> WorkspaceConfig:
    return WorkspaceConfig.from_env()


@mcp.tool(
    title="列出知识库",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def list_knowledge_base() -> KnowledgeInventory:
    """列出本地知识库各分类中的可读取文件，不读取文件正文。"""

    return list_knowledge(_config())


@mcp.tool(
    title="检索本地知识库",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def search_knowledge_base(
    query: Annotated[str, Field(min_length=1, description="公司名称或核心检索词")],
    keywords: Annotated[
        list[str] | None,
        Field(description="可选的补充关键词，例如行业、评估方法或准则主题"),
    ] = None,
    categories: Annotated[
        list[str] | None,
        Field(description="限定分类：准则、评估报告、评估说明、公司档案"),
    ] = None,
    limit: Annotated[int, Field(ge=1, le=50, description="最多返回的命中数量")] = 20,
) -> SearchResponse:
    """在本地 Markdown、文本、PDF 与 DOCX 知识文件中检索并返回上下文片段。"""

    return search_knowledge(
        _config(),
        query=query,
        keywords=keywords,
        categories=categories,
        limit=limit,
    )


@mcp.tool(
    title="准备联网调研",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def prepare_web_research(
    company_name: Annotated[str, Field(min_length=1, description="目标公司全称或常用名称")],
    focus: Annotated[
        list[str] | None,
        Field(description="可选调研重点，例如主营业务、股权结构、财务数据、行业地位"),
    ] = None,
) -> ResearchPlan:
    """生成供宿主执行的联网检索计划；本工具自身不联网，也不保存检索结果。"""

    return build_research_plan(company_name, focus)


@mcp.tool(
    title="起草企业价值评估报告",
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    ),
)
def draft_valuation_report(request: DraftReportRequest) -> WriteResult:
    """将已核验的结构化资料写成 Markdown 报告初稿；缺失项会保留人工补充标记。"""

    return write_valuation_report(_config(), request)


@mcp.tool(
    title="检查报告合规性",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def check_report_compliance(
    report_path: Annotated[
        str,
        Field(description="工作区内的 Markdown 相对路径，例如 reports/示例报告.md"),
    ],
) -> ComplianceResult:
    """检查章节、方法说明、来源标注与人工复核提示，并给出检查清单。"""

    return run_compliance_check(_config(), report_path)


@mcp.tool(
    title="更新公司知识档案",
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    ),
)
def update_company_knowledge(request: CompanyKnowledgeRequest) -> WriteResult:
    """把带来源链接的新公开信息写入知识库的公司档案目录。"""

    return write_company_knowledge(_config(), request)


@mcp.resource("valuation://instructions", name="工作流说明")
def workflow_instructions() -> str:
    """返回本服务推荐的完整工作流与专业边界。"""

    return SERVER_INSTRUCTIONS


@mcp.resource("valuation://report-template", name="报告章节模板")
def report_template() -> str:
    """返回企业价值评估报告初稿的标准章节顺序。"""

    return """# 企业价值评估报告初稿

1. 报告声明
2. 摘要
3. 委托方及被评估单位概况
4. 评估目的与评估对象
5. 评估基准日
6. 评估方法与价值类型
7. 评估假设与限制条件
8. 评估结论
9. 特别事项说明
10. 数据来源与参考资料
11. 人工复核清单
"""


@mcp.prompt(title="执行完整企业价值评估报告工作流")
def full_valuation_workflow(company_name: str) -> str:
    """生成由 MCP 工具驱动的完整工作流提示词。"""

    steps = [
        f"请为“{company_name}”准备企业价值评估报告初稿：",
        (
            "1. 调用 list_knowledge_base 与 search_knowledge_base，"
            "检索公司信息、同行业案例和适用准则；"
        ),
        (
            "2. 若本地信息不足，调用 prepare_web_research，并用宿主的联网能力核验官方网站、"
            "监管披露和年度报告，逐项保留 URL 与日期；"
        ),
        "3. 不得补造缺失数据。将已核验资料整理为 DraftReportRequest，调用 draft_valuation_report；",
        "4. 调用 check_report_compliance，将未通过项和需人工复核项写入交付说明；",
        (
            "5. 仅将已核验、可公开且来源明确的新资料整理为 CompanyKnowledgeRequest，"
            "调用 update_company_knowledge；"
        ),
        "6. 明确说明该初稿不构成正式资产评估意见，最终结论须由专业人员复核、签字并承担责任。",
    ]
    return "\n".join(steps) + "\n"


def main() -> None:
    """Run the local STDIO MCP transport."""

    mcp.run()


if __name__ == "__main__":
    main()
