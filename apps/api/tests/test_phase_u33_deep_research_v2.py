import pytest
from app.services.research.deep_research_v2 import deep_research_v2, DeepResearchGraph


@pytest.mark.asyncio
async def test_iterative_deep_research_v2():
    topic = "Ứng dụng Trí tuệ Nhân tạo trong Ngân hàng Số 2026"
    graph = await deep_research_v2.execute_iterative_research(topic=topic, max_hops=2)

    assert isinstance(graph, DeepResearchGraph)
    assert graph.topic == topic
    assert len(graph.subquestions) >= 3
    assert len(graph.evidence_nodes) >= 3

    # Verify Multi-Hop levels
    hops = [e.hop_level for e in graph.evidence_nodes]
    assert 1 in hops
    assert 2 in hops

    # Verify Evidence provenance & freshness
    for ev in graph.evidence_nodes:
        assert ev.source_url.startswith("https://")
        assert ev.reliability_score >= 0.50
        assert len(ev.freshness_date) > 0

    assert len(graph.synthesis_report) > 10
    assert graph.total_sources_cross_checked >= 3
