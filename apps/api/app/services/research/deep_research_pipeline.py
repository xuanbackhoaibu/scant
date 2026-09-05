import time
import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.services.research.academic.base import ResearchSourceModel
from app.services.research.academic.crossref_provider import CrossrefProvider
from app.services.research.academic.arxiv_provider import ArxivProvider
from app.services.research.academic.semantic_scholar_provider import SemanticScholarProvider
from app.services.research.academic.pubmed_provider import PubMedProvider
from app.services.research.web_search import web_search_provider
from app.services.research.query_analyzer import query_analyzer, QueryAnalysisResult
from app.services.research.source_verifier import source_verifier
from app.services.research.quality_scorer import source_quality_scorer
from app.services.research.evidence_extractor import evidence_extractor, EvidenceItemModel, MarketDataClaim
from app.services.research.synthesis_agent import synthesis_agent, ResearchSynthesisReport


class DeepResearchGraphNode(BaseModel):
    id: str
    label: str
    type: str  # query | subtopic | source | evidence
    data: Dict[str, Any] = Field(default_factory=dict)


class DeepResearchGraphEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class DeepResearchResult(BaseModel):
    session_id: str
    query: str
    mode: str  # quick | deep | expert
    analysis: QueryAnalysisResult
    total_found: int
    total_verified: int
    academic_count: int
    government_count: int
    market_count: int
    news_count: int
    sources: List[ResearchSourceModel]
    evidence_nodes: List[EvidenceItemModel]
    market_claims: List[MarketDataClaim]
    synthesis: ResearchSynthesisReport
    graph_nodes: List[DeepResearchGraphNode] = Field(default_factory=list)
    graph_edges: List[DeepResearchGraphEdge] = Field(default_factory=list)
    search_log: List[Dict[str, Any]] = Field(default_factory=list)
    duration_seconds: float = 0.0


class DeepResearchPipeline:
    """
    Complete Autonomous Deep Research Pipeline (Sections 1 through 25).
    Runs real discovery, verification, deduplication, quality scoring, evidence extraction,
    and anti-hallucination synthesis.
    """

    def __init__(self):
        self.crossref = CrossrefProvider()
        self.arxiv = ArxivProvider()
        self.semantic_scholar = SemanticScholarProvider()
        self.pubmed = PubMedProvider()
        self.web = web_search_provider
        self._cache: Dict[str, Tuple[float, DeepResearchResult]] = {}
        self.CACHE_TTL = 3600  # 1 hour query cache

    async def execute(
        self,
        query: str,
        mode: str = "deep",
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> DeepResearchResult:
        start_time = time.time()
        session_id = f"research_{int(start_time)}_{hash(query) % 100000}"
        cache_key = f"{query.strip().lower()}_{mode}"

        # 0. Check cache
        if cache_key in self._cache:
            ts, cached_res = self._cache[cache_key]
            if time.time() - ts < self.CACHE_TTL:
                if on_progress:
                    on_progress(100, "Đã tải kết quả từ bộ nhớ đệm (Cache Hit).")
                return cached_res

        search_logs: List[Dict[str, Any]] = []

        def log_step(provider: str, message: str, count: int = 0):
            search_logs.append({
                "timestamp": round(time.time() - start_time, 2),
                "provider": provider,
                "message": message,
                "count": count,
            })

        # Step 1: Query Understanding & Expansion
        if on_progress:
            on_progress(10, "Đang phân tích câu hỏi & mở rộng từ khóa song ngữ...")
        log_step("query_analyzer", "Bắt đầu phân tích cấu trúc truy vấn")
        analysis = await query_analyzer.analyze_and_expand(query)
        log_step(
            "query_analyzer",
            f"Đã mở rộng {len(analysis.keywords_vi)} từ khóa tiếng Việt và {len(analysis.keywords_en)} từ khóa tiếng Anh",
        )

        # Determine target limits based on depth (Section 29)
        # Quick (~5-10), Deep (~15-25), Expert (25+)
        provider_limit = 4 if mode == "quick" else 8 if mode == "deep" else 15

        # Step 2: Multi-Provider Source Discovery
        if on_progress:
            on_progress(25, "Đang tìm kiếm nguồn học thuật (Crossref, ArXiv, Semantic Scholar)...")

        search_tasks = []

        # Crossref search (English + Vietnamese keywords)
        search_query_en = analysis.keywords_en[0] if analysis.keywords_en else query
        search_tasks.append(self.crossref.search(search_query_en, limit=provider_limit))

        # arXiv search
        search_tasks.append(self.arxiv.search(search_query_en, limit=provider_limit))

        # Semantic Scholar search
        search_tasks.append(self.semantic_scholar.search(search_query_en, limit=provider_limit))

        # PubMed search if applicable
        if PubMedProvider.is_medical_query(query) or "healthcare" in analysis.topic.lower():
            search_tasks.append(self.pubmed.search(search_query_en, limit=provider_limit))

        # Web search (Official portals, market reports, government agencies)
        if on_progress:
            on_progress(40, "Đang tìm kiếm báo cáo thị trường & web uy tín...")
        web_query = analysis.keywords_vi[0] if analysis.keywords_vi else query
        search_tasks.append(self.web.search(web_query, limit=provider_limit))

        # Run all discovery tasks concurrently with resilience
        discovery_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        raw_sources: List[ResearchSourceModel] = []
        for res in discovery_results:
            if isinstance(res, list):
                raw_sources.extend(res)

        log_step("discovery", f"Thu thập được tổng cộng {len(raw_sources)} nguồn thô từ các provider", len(raw_sources))

        # Step 3: Deduplication & Metadata Merge (Section 8)
        if on_progress:
            on_progress(55, "Đang loại bỏ nguồn trùng lặp & hợp nhất metadata...")
        deduped_sources = source_verifier.deduplicate_and_merge(raw_sources)
        log_step("deduplication", f"Sau khi lọc trùng: còn lại {len(deduped_sources)} nguồn duy nhất", len(deduped_sources))

        # Step 4: Verification & Live HTTP Probing (Section 7)
        if on_progress:
            on_progress(70, "Đang xác minh liên kết HTTP & định dạng DOI...")
        verified_sources = await source_verifier.verify_sources_batch(deduped_sources)

        # Step 5: Transparent Quality Scoring (Section 9, 10, 11)
        if on_progress:
            on_progress(80, "Đang tính toán Điểm chất lượng nguồn (Source Quality Score)...")
        scored_sources = source_quality_scorer.score_sources(query, verified_sources)

        # Slice to max required sources based on mode
        max_target = 8 if mode == "quick" else 18 if mode == "deep" else 32
        final_sources = scored_sources[:max_target]

        # Step 6: Evidence & Quantitative Fact Extraction (Section 12)
        if on_progress:
            on_progress(88, "Đang trích xuất đoạn bằng chứng & số liệu thống kê...")
        evidence_nodes, market_claims = evidence_extractor.extract_evidence_from_sources(query, final_sources)
        log_step("evidence_extractor", f"Đã trích xuất {len(evidence_nodes)} bằng chứng & {len(market_claims)} số liệu")

        # Step 7: Strict Anti-Hallucination AI Synthesis (Section 13, 14, 19)
        if on_progress:
            on_progress(95, "Đang tổng hợp báo cáo nghiên cứu & đối chiếu citation...")
        synthesis_report = await synthesis_agent.synthesize(query, final_sources, evidence_nodes, market_claims)

        # Step 8: Build Research Graph Visualization (Section 21)
        graph_nodes, graph_edges = self._build_research_graph(query, analysis, final_sources, evidence_nodes)

        # Calculate statistics
        academic_count = sum(1 for s in final_sources if s.source_type == "academic" or s.doi or s.arxiv_id or s.pmid)
        gov_count = sum(1 for s in final_sources if s.source_type == "government" or ".gov" in s.url)
        market_count = sum(1 for s in final_sources if s.source_type in ("market", "industry_report", "company"))
        news_count = sum(1 for s in final_sources if s.source_type in ("news", "reputable_news", "web"))
        verified_count = sum(1 for s in final_sources if s.metadata_verified or s.url_verified)

        duration = round(time.time() - start_time, 2)
        log_step("pipeline", f"Hoàn tất nghiên cứu chuyên sâu trong {duration} giây", len(final_sources))

        if on_progress:
            on_progress(100, "Nghiên cứu hoàn tất.")

        result = DeepResearchResult(
            session_id=session_id,
            query=query,
            mode=mode,
            analysis=analysis,
            total_found=len(raw_sources),
            total_verified=verified_count,
            academic_count=academic_count,
            government_count=gov_count,
            market_count=market_count,
            news_count=news_count,
            sources=final_sources,
            evidence_nodes=evidence_nodes,
            market_claims=market_claims,
            synthesis=synthesis_report,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            search_log=search_logs,
            duration_seconds=duration,
        )

        # Save to memory cache
        self._cache[cache_key] = (time.time(), result)
        return result

    def _build_research_graph(
        self,
        query: str,
        analysis: QueryAnalysisResult,
        sources: List[ResearchSourceModel],
        evidence_nodes: List[EvidenceItemModel],
    ) -> Tuple[List[DeepResearchGraphNode], List[DeepResearchGraphEdge]]:
        nodes: List[DeepResearchGraphNode] = []
        edges: List[DeepResearchGraphEdge] = []

        # Root Node: Query
        nodes.append(DeepResearchGraphNode(id="root", label=query, type="query"))

        # Subtopic Nodes
        subtopics = [
            ("sub_academic", "Nghiên cứu Học thuật & Công nghệ"),
            ("sub_market", "Quy mô & Thống kê Thị trường"),
            ("sub_policy", "Chính sách & Pháp lý Quốc gia"),
        ]
        for sub_id, sub_label in subtopics:
            nodes.append(DeepResearchGraphNode(id=sub_id, label=sub_label, type="subtopic"))
            edges.append(DeepResearchGraphEdge(source="root", target=sub_id))

        # Link Sources to Subtopics
        for i, s in enumerate(sources[:8]):
            src_node_id = f"node_src_{i + 1}"
            label = f"[{i + 1}] {s.title[:40]}..."
            nodes.append(DeepResearchGraphNode(id=src_node_id, label=label, type="source", data={"url": s.url}))

            target_sub = "sub_academic" if s.source_type == "academic" else (
                "sub_policy" if s.source_type == "government" else "sub_market"
            )
            edges.append(DeepResearchGraphEdge(source=target_sub, target=src_node_id))

            # Link first evidence chunk if exists
            ev_match = next((e for e in evidence_nodes if e.source_id == s.id), None)
            if ev_match:
                ev_node_id = f"node_ev_{i + 1}"
                nodes.append(DeepResearchGraphNode(
                    id=ev_node_id,
                    label=f"Bằng chứng: {ev_match.text[:40]}...",
                    type="evidence",
                    data={"full_text": ev_match.text}
                ))
                edges.append(DeepResearchGraphEdge(source=src_node_id, target=ev_node_id))

        return nodes, edges


deep_research_pipeline = DeepResearchPipeline()
