import re
from typing import Any, Dict, List


class ReportContextBuilder:
    """Builds a scoped, grounded context for one report section."""

    FACT_TYPE_KEYWORDS = {
        "employee": ["nhân viên", "employee", "nhan vien"],
        "department": ["phòng ban", "department", "phong ban"],
        "role": ["chức vụ", "role", "position", "chuc vu"],
        "salary": ["lương", "salary", "thực lĩnh", "thu nhập", "luong", "income"],
        "tax": ["thuế", "tax", "tncn"],
        "insurance": ["bhxh", "bhyt", "bhtn", "bảo hiểm", "insurance"],
        "working_days": ["ngày công", "working day", "cong"],
        "bonus": ["thưởng", "bonus"],
        "allowance": ["phụ cấp", "allowance"],
        "deduction": ["khấu trừ", "deduction"],
        "summary": ["tổng", "trung bình", "cao nhất", "thấp nhất", "sum", "average", "max", "min"],
    }

    @classmethod
    def build_entity_whitelist(cls, profiles: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        entities = {
            "departments": set(),
            "roles": set(),
            "employees": set(),
            "sheet_names": set(),
            "column_names": set(),
        }
        for profile in profiles or []:
            for sheet in profile.get("sheets", []):
                if sheet.get("name"):
                    entities["sheet_names"].add(str(sheet["name"]))
                for col in sheet.get("columns", []):
                    col_name = str(col.get("name") or "")
                    if col_name:
                        entities["column_names"].add(col_name)
                    lower = col_name.lower()
                    top_values = [str(x.get("value")) for x in col.get("top_values", []) if x.get("value")]
                    samples = [str(x) for x in col.get("sample_values", []) if x]
                    values = top_values or samples
                    if any(k in lower for k in ["phòng", "department", "bộ phận"]):
                        entities["departments"].update(values)
                    elif any(k in lower for k in ["chức", "role", "position", "vị trí"]):
                        entities["roles"].update(values)
                    elif any(k in lower for k in ["nhân viên", "employee", "họ tên", "name", "ten"]):
                        entities["employees"].update(values)
        return {key: sorted(value)[:200] for key, value in entities.items()}

    @classmethod
    def classify_fact(cls, fact: Dict[str, Any]) -> str:
        text = f"{fact.get('name') or fact.get('fact') or ''} {fact.get('source') or ''}".lower()
        matched = [name for name, keys in cls.FACT_TYPE_KEYWORDS.items() if any(key in text for key in keys)]
        return matched[0] if matched else "general"

    @classmethod
    def _fact_is_allowed(cls, fact_type: str, allowed_types: List[str]) -> bool:
        if fact_type in ["row_count", "column_count", "general", "formula"]:
            return True
        return any(fact_type == allowed or fact_type.startswith(f"{allowed}_") for allowed in allowed_types if allowed != "general")

    @classmethod
    def section_allowed_fact_types(cls, section_title: str) -> List[str]:
        title = (section_title or "").lower()
        allowed = ["general", "summary"]
        for fact_type, keys in cls.FACT_TYPE_KEYWORDS.items():
            if any(key in title for key in keys):
                allowed.append(fact_type)
        if "salary" in allowed:
            allowed.extend(["working_days", "tax", "insurance", "bonus", "allowance", "deduction", "department", "role"])
        if len(allowed) == 2:
            if any(k in title for k in ["phân tích", "thống kê", "dữ liệu", "kpi", "tổng quan"]):
                allowed.extend(["employee", "department", "role", "salary", "tax", "insurance", "working_days", "bonus", "allowance", "deduction"])
        return sorted(set(allowed))

    @classmethod
    def build_for_section(
        cls,
        section: Any,
        dataset_profiles: List[Dict[str, Any]],
        template_context: Dict[str, Any],
        max_facts: int = 36,
    ) -> Dict[str, Any]:
        allowed_types = cls.section_allowed_fact_types(getattr(section, "title", ""))
        all_facts: List[Dict[str, Any]] = []
        chart_specs: List[Dict[str, Any]] = []
        formula_evidence: List[Dict[str, Any]] = []
        rows: List[Dict[str, Any]] = []

        for profile in dataset_profiles or []:
            for fact in profile.get("verified_facts", []):
                fact_type = fact.get("fact_type") or cls.classify_fact(fact)
                normalized = {**fact, "fact_type": fact_type}
                if cls._fact_is_allowed(fact_type, allowed_types):
                    all_facts.append(normalized)
            for sheet in profile.get("sheets", []):
                for cell, formula in (sheet.get("formulas") or {}).items():
                    formula_evidence.append({"sheet": sheet.get("name"), "cell": cell, "formula": formula})
                if not rows:
                    rows = sheet.get("records", [])[:12]
                for grouped in sheet.get("grouped_statistics", []):
                    metric = str(grouped.get("metric") or "")
                    group_by = str(grouped.get("group_by") or "")
                    metric_type = cls.classify_fact({"name": metric})
                    if not cls._fact_is_allowed(f"{metric_type}_grouped", allowed_types):
                        continue
                    stats = grouped.get("statistics", [])[:8]
                    labels = [str(item.get("group")) for item in stats if item.get("group") is not None]
                    values = [item.get("sum") for item in stats if item.get("sum") is not None]
                    if len(labels) >= 2 and len(labels) == len(values):
                        chart_specs.append({
                            "kind": "chart",
                            "chart_type": "bar",
                            "title": f"Tổng {metric} theo {group_by}",
                            "labels": labels,
                            "values": values,
                            "unit": "",
                            "source": f"{sheet.get('name')}!{group_by}+{metric}",
                        })

        selected_facts = all_facts[:max_facts]
        source_ranges = []
        for fact in selected_facts:
            source = fact.get("source")
            if isinstance(source, dict):
                rng = source.get("range") or source.get("cell")
            else:
                rng = source
            if rng:
                source_ranges.append(str(rng))

        prompt_lines = [
            "SECTION-SCOPED GROUNDED CONTEXT",
            f"Section: {getattr(section, 'title', '')}",
            f"Allowed fact types: {', '.join(allowed_types)}",
            "Verified facts allowed for this section:",
        ]
        for fact in selected_facts:
            name = fact.get("name") or fact.get("fact")
            value = fact.get("value")
            source = fact.get("source")
            if isinstance(source, dict):
                source_text = f"{source.get('file', '')}/{source.get('sheet', '')}!{source.get('range', '')}"
            else:
                source_text = str(source)
            prompt_lines.append(f"- {fact.get('id')}: {name} = {value} [source: {source_text}]")
        if formula_evidence:
            prompt_lines.append("Formula evidence:")
            for item in formula_evidence[:20]:
                prompt_lines.append(f"- {item['sheet']}!{item['cell']}: {item['formula']}")
        prompt_lines.append("Only use the facts above for numbers/entities in this section.")
        if chart_specs:
            prompt_lines.append("Grounded chart candidates:")
            for spec in chart_specs[:3]:
                labels = ",".join(str(x) for x in spec["labels"])
                values = ",".join(str(x) for x in spec["values"])
                prompt_lines.append(f"- [[CHART:type={spec['chart_type']};title={spec['title']};labels={labels};values={values};unit={spec['unit']}]] [source: {spec['source']}]")
        if rows:
            prompt_lines.append("Representative source rows from the uploaded dataset:")
            for idx, row in enumerate(rows[:8], 1):
                compact = ", ".join(f"{key}={value}" for key, value in list(row.items())[:12])
                prompt_lines.append(f"- Row {idx}: {compact}")

        return {
            "section": {"id": getattr(section, "section_number", None) or getattr(section, "id", ""), "title": getattr(section, "title", "")},
            "allowed_fact_types": allowed_types,
            "verified_facts": selected_facts,
            "dataset_profiles": dataset_profiles,
            "relevant_rows": rows,
            "formula_evidence": formula_evidence[:30],
            "chart_specs": chart_specs[:5],
            "allowed_entities": cls.build_entity_whitelist(dataset_profiles),
            "writing_style": {
                "template_headings": [h.get("text") for h in template_context.get("headings", [])[:30]],
                "sample_content_removed": template_context.get("sample_content_removed", False),
            },
            "facts_used": [fact.get("id") for fact in selected_facts],
            "source_ranges": source_ranges[:80],
            "prompt": "\n".join(prompt_lines),
        }


report_context_builder = ReportContextBuilder()
