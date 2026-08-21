from typing import Any, Dict, List, Set, Optional


class DependencyGraphService:
    """
    Report Dependency Graph and Granular Stale Invalidation (Phase U17).
    Maintains DAG of data dependencies and determines exact stale sections upon data updates.
    """

    def __init__(self):
        # report_id -> { node_id -> set of dependent_node_ids }
        self._graphs: Dict[str, Dict[str, Set[str]]] = {}
        # report_id -> set of stale_node_ids
        self._stale_nodes: Dict[str, Set[str]] = {}

    def register_dependency(self, report_id: str, source_node: str, target_node: str):
        if report_id not in self._graphs:
            self._graphs[report_id] = {}
        if source_node not in self._graphs[report_id]:
            self._graphs[report_id][source_node] = set()

        self._graphs[report_id][source_node].add(target_node)

    def invalidate_source(self, report_id: str, source_node: str) -> Set[str]:
        """Traverses DAG to mark all downstream dependent sections/blocks as stale."""
        if report_id not in self._graphs:
            return set()

        stale: Set[str] = set()
        queue = [source_node]

        while queue:
            curr = queue.pop(0)
            dependents = self._graphs[report_id].get(curr, set())
            for dep in dependents:
                if dep not in stale:
                    stale.add(dep)
                    queue.append(dep)

        if report_id not in self._stale_nodes:
            self._stale_nodes[report_id] = set()

        self._stale_nodes[report_id].update(stale)
        return stale

    def get_stale_sections(self, report_id: str) -> List[str]:
        return list(self._stale_nodes.get(report_id, set()))

    def clear_stale(self, report_id: str, section_id: Optional[str] = None):
        if report_id in self._stale_nodes:
            if section_id:
                self._stale_nodes[report_id].discard(section_id)
            else:
                self._stale_nodes[report_id].clear()


dependency_graph_service = DependencyGraphService()
