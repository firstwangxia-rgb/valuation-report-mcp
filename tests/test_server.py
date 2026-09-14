from __future__ import annotations

import pytest
from mcp import Client

from valuation_report_mcp.server import mcp


@pytest.mark.anyio
async def test_mcp_client_can_call_research_tool() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "prepare_web_research",
            {"company_name": "示例科技", "focus": ["核心专利"]},
        )

    assert result.is_error is False
    assert result.structured_content["company_name"] == "示例科技"
    assert any("核心专利" in query for query in result.structured_content["queries"])


@pytest.mark.anyio
async def test_mcp_exposes_expected_tools() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()

    names = {tool.name for tool in tools.tools}
    assert names == {
        "list_knowledge_base",
        "search_knowledge_base",
        "prepare_web_research",
        "draft_valuation_report",
        "check_report_compliance",
        "update_company_knowledge",
    }
