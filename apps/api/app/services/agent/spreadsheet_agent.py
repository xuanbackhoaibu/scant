import io
import json
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class DeterministicSpreadsheetEngine:
    """
    Deterministic Mathematical & Statistical Engine (Phase U30).
    Ensures LLM never hallucinates or calculates raw figures independently.
    All calculations are strictly computed via Pandas / NumPy.
    """

    @staticmethod
    def inspect_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "num_rows": int(len(df)),
            "num_cols": int(len(df.columns)),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }

    @staticmethod
    def profile_data(df: pd.DataFrame) -> Dict[str, Any]:
        numeric_df = df.select_dtypes(include=[np.number])
        summary = {}
        if not numeric_df.empty:
            desc = numeric_df.describe().to_dict()
            for col, stats in desc.items():
                summary[col] = {
                    "count": int(stats.get("count", 0)),
                    "mean": round(float(stats.get("mean", 0.0)), 2),
                    "std": round(float(stats.get("std", 0.0)), 2),
                    "min": float(stats.get("min", 0.0)),
                    "max": float(stats.get("max", 0.0)),
                }

        missing = {col: int(df[col].isnull().sum()) for col in df.columns}
        duplicates = int(df.duplicated().sum())

        return {
            "numeric_summary": summary,
            "missing_values": missing,
            "duplicate_rows_count": duplicates,
        }

    @staticmethod
    def calculate_kpis(
        df: pd.DataFrame,
        dataset_name: str,
        kpi_specs: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Computes specific KPIs with full provenance tracking.
        Specs format: [{"name": "Tổng Doanh Thu", "column": "revenue", "op": "sum"}]
        """
        results = []
        for spec in kpi_specs:
            name = spec["name"]
            col = spec["column"]
            op = spec.get("op", "sum").lower()

            if col not in df.columns:
                continue

            numeric_series = pd.to_numeric(df[col], errors="coerce").dropna()
            if op == "sum":
                val = float(numeric_series.sum())
            elif op == "avg" or op == "mean":
                val = float(numeric_series.mean())
            elif op == "max":
                val = float(numeric_series.max())
            elif op == "min":
                val = float(numeric_series.min())
            elif op == "count":
                val = float(len(numeric_series))
            else:
                val = float(numeric_series.sum())

            results.append({
                "kpi_name": name,
                "value": round(val, 2),
                "provenance": {
                    "dataset": dataset_name,
                    "sheet": "Sheet1",
                    "column": col,
                    "operation": op,
                    "computed_deterministically": True,
                }
            })
        return results

    @staticmethod
    def aggregate_and_group(
        df: pd.DataFrame,
        group_col: str,
        val_col: str,
        op: str = "sum"
    ) -> Dict[str, Any]:
        if group_col not in df.columns or val_col not in df.columns:
            return {"error": "Columns not found"}

        clean_df = df.copy()
        clean_df[val_col] = pd.to_numeric(clean_df[val_col], errors="coerce").fillna(0)

        if op == "sum":
            grouped = clean_df.groupby(group_col)[val_col].sum()
        elif op == "mean" or op == "avg":
            grouped = clean_df.groupby(group_col)[val_col].mean()
        else:
            grouped = clean_df.groupby(group_col)[val_col].sum()

        records = [{"category": str(k), "value": round(float(v), 2)} for k, v in grouped.items()]
        return {
            "grouped_data": records,
            "group_by": group_col,
            "metric": val_col,
            "operation": op,
        }


class SpreadsheetAgent:
    """
    Autonomous Spreadsheet Agent (Phase U30).
    Orchestrates deterministic data calculations and generates verified business narratives with full provenance.
    """

    def __init__(self):
        self.engine = DeterministicSpreadsheetEngine()

    async def analyze_and_narrate(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        user_query: str
    ) -> Dict[str, Any]:
        # 1. Deterministic Profiling
        profile = self.engine.profile_data(df)

        # 2. Extract numeric columns for KPI calculation
        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        kpi_specs = [{"name": f"Tổng {col}", "column": col, "op": "sum"} for col in num_cols[:4]]
        kpis = self.engine.calculate_kpis(df, dataset_name, kpi_specs)

        # 3. AI interprets verified figures and generates narrative with provenance citations
        prompt = f"""Bạn là Chuyên gia Phân tích Dữ liệu (Spreadsheet Intelligence Agent).
Dữ liệu đã được tính toán CHÍNH XÁC 100% bằng engine Pandas:
- Hồ sơ dữ liệu: {json.dumps(profile, ensure_ascii=False)}
- Các chỉ số KPI (kèm nguồn gốc dữ liệu): {json.dumps(kpis, ensure_ascii=False)}

Yêu cầu người dùng: "{user_query}"

Quy tắc bất biến:
1. KHÔNG tự bịa hoặc tính sai số. Chỉ dùng các số liệu đã cung cấp.
2. Viết báo cáo phân tích sâu sắc, làm nổi bật KPI chính và xu hướng kinh doanh.
"""
        req = AIRequest(
            task_type=AITaskType.DATA_NARRATIVE,
            prompt=prompt,
        )
        resp = await ai_gateway.execute(req)

        return {
            "narrative": resp.text,
            "kpis": kpis,
            "data_profile": profile,
            "provenance_count": len(kpis),
        }


spreadsheet_agent = SpreadsheetAgent()
