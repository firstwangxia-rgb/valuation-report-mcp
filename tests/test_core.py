from __future__ import annotations

from pathlib import Path

import pytest

from valuation_report_mcp.core import (
    WorkspaceConfig,
    check_compliance,
    list_knowledge,
    prepare_research_plan,
    resolve_within,
    search_knowledge,
    write_company_knowledge,
    write_report,
)
from valuation_report_mcp.schemas import (
    CompanyKnowledgeRequest,
    DraftReportRequest,
    SourceLink,
)


@pytest.fixture
def workspace(tmp_path: Path) -> WorkspaceConfig:
    knowledge_base = tmp_path / "knowledge-base"
    for category in ("准则", "评估报告", "评估说明", "公司档案"):
        (knowledge_base / category).mkdir(parents=True)
    reports = tmp_path / "reports"
    reports.mkdir()
    return WorkspaceConfig(root=tmp_path, knowledge_base=knowledge_base, reports=reports)


def sample_report_request(**changes: object) -> DraftReportRequest:
    values: dict[str, object] = {
        "company_name": "示例科技有限公司",
        "valuation_purpose": "股权交易定价参考",
        "valuation_date": "2025-12-31",
        "company_profile": "公司从事工业机器人研发与销售。",
        "financial_data": "2025年数据以经审计财务报表为准。",
        "industry_comparison": "可比口径需进一步核验。",
        "method_analysis": "拟采用收益法和市场法，资产基础法作为适用性分析对象。",
        "preliminary_conclusion": "评估结论待完成测算后补充。",
        "sources": [SourceLink(title="示例来源", url="https://example.com/annual-report")],
    }
    values.update(changes)
    return DraftReportRequest(**values)


def test_resolve_within_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        resolve_within(tmp_path, "../outside.md")
    with pytest.raises(ValueError, match="absolute"):
        resolve_within(tmp_path, tmp_path / "absolute.md")


def test_search_and_inventory(workspace: WorkspaceConfig) -> None:
    file_path = workspace.knowledge_base / "公司档案" / "示例科技.md"
    file_path.write_text(
        "# 示例科技\n主营业务为工业机器人，财务数据来源：https://example.com/report",
        encoding="utf-8",
    )

    result = search_knowledge(
        workspace,
        query="示例科技",
        keywords=["工业机器人"],
        categories=["公司档案"],
    )

    assert result.searched_files == 1
    assert result.skipped_files == 0
    assert len(result.hits) == 1
    assert result.hits[0].category == "公司档案"
    assert result.hits[0].path == "knowledge-base/公司档案/示例科技.md"
    assert result.hits[0].matched_terms == ["示例科技", "工业机器人"]

    inventory = list_knowledge(workspace)
    counts = {item.name: item.file_count for item in inventory.categories}
    assert counts["公司档案"] == 1
    assert counts["准则"] == 0


def test_search_rejects_unknown_category(workspace: WorkspaceConfig) -> None:
    with pytest.raises(ValueError, match="unsupported categories"):
        search_knowledge(workspace, "示例", categories=["其他"])


def test_prepare_research_plan_is_source_focused() -> None:
    plan = prepare_research_plan("示例科技", ["核心专利"])

    assert plan.local_check_first is True
    assert any("年度报告" in query for query in plan.queries)
    assert any("核心专利" in query for query in plan.queries)
    assert any("监管机构" in source for source in plan.preferred_sources)
    assert "URL" in plan.host_instruction


def test_write_report_then_check_compliance(workspace: WorkspaceConfig) -> None:
    result = write_report(workspace, sample_report_request())

    assert result.status == "created"
    output = Path(result.path)
    assert output.exists()
    assert output.parent == workspace.reports
    assert result.bytes_written == len(output.read_bytes())

    compliance = check_compliance(workspace, f"reports/{output.name}")
    assert compliance.overall_status == "通过（初稿自检）"
    assert compliance.missing_sections == []
    assert compliance.source_url_count == 1
    assert "收益法" in compliance.detected_methods
    assert any(item.item == "最终结论" for item in compliance.manual_review_items)


def test_report_write_requires_overwrite_for_changed_file(workspace: WorkspaceConfig) -> None:
    initial = sample_report_request()
    first = write_report(workspace, initial)
    unchanged = write_report(workspace, initial)

    assert first.status == "created"
    assert unchanged.status == "unchanged"

    changed = sample_report_request(preliminary_conclusion="新结论", overwrite=True)
    replaced = write_report(workspace, changed)
    assert replaced.status == "written"
    assert "新结论" in Path(replaced.path).read_text(encoding="utf-8")


def test_update_company_knowledge_requires_source_url(workspace: WorkspaceConfig) -> None:
    request = CompanyKnowledgeRequest(
        company_name="示例科技有限公司",
        information_date="2026-09-07",
        industry="智能制造",
        business_description="公司从事工业机器人研发。",
        financial_performance="数据待审计报告核验。",
        industry_comparison="同行业口径待复核。",
        sources=[SourceLink(title="官方网站", url="https://example.com/")],
    )

    result = write_company_knowledge(workspace, request)
    output = Path(result.path)

    assert result.status == "created"
    assert output.parent == workspace.knowledge_base / "公司档案"
    assert "https://example.com/" in output.read_text(encoding="utf-8")


def test_report_filename_cannot_escape_reports_directory(workspace: WorkspaceConfig) -> None:
    request = sample_report_request(output_filename="../outside.md")

    with pytest.raises(ValueError, match="must be a filename"):
        write_report(workspace, request)
    assert not (workspace.root / "outside.md").exists()
