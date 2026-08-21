import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class DataAnalysisEngine:
    """
    Python-powered Data Analysis & Statistical Aggregation Engine.
    Enforces strict mathematical accuracy (AI never invents totals or averages).
    """

    @classmethod
    def load_dataframe(cls, file_path: str) -> pd.DataFrame:
        ext = Path(file_path).suffix.lower()
        if ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        elif ext == ".csv":
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported tabular format: {ext}")

    @classmethod
    def profile_dataset(cls, file_path: str) -> Dict[str, Any]:
        df = cls.load_dataframe(file_path)
        
        # Total rows & cols
        total_rows, total_cols = df.shape
        missing_count = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        columns_profile: List[Dict[str, Any]] = []
        for col in df.columns:
            series = df[col]
            dtype_str = str(series.dtype)
            is_numeric = pd.api.types.is_numeric_dtype(series)
            null_pct = round(float(series.isnull().mean() * 100), 1)

            col_info: Dict[str, Any] = {
                "name": str(col),
                "type": "numeric" if is_numeric else "text" if "object" in dtype_str or "str" in dtype_str else "datetime" if "datetime" in dtype_str else "boolean",
                "null_percentage": null_pct,
                "unique_count": int(series.nunique()),
            }

            if is_numeric:
                clean_s = series.dropna()
                if len(clean_s) > 0:
                    col_info["min"] = float(clean_s.min())
                    col_info["max"] = float(clean_s.max())
                    col_info["mean"] = round(float(clean_s.mean()), 2)
                    col_info["sum"] = round(float(clean_s.sum()), 2)

            columns_profile.append(col_info)

        # Preview first 10 rows
        preview_data = df.head(10).replace({np.nan: None}).to_dict(orient="records")

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "missing_values_count": missing_count,
            "duplicate_rows_count": duplicate_rows,
            "columns": columns_profile,
            "preview_rows": preview_data,
        }

    @classmethod
    def aggregate_data(
        cls,
        file_path: str,
        group_by: Optional[str] = None,
        metric_column: Optional[str] = None,
        aggregation: str = "sum",  # sum, mean, count, min, max
        top_n: int = 10
    ) -> Dict[str, Any]:
        df = cls.load_dataframe(file_path)

        if not group_by or not metric_column:
            # Overall metric
            if metric_column and metric_column in df.columns:
                s = pd.to_numeric(df[metric_column], errors="coerce").dropna()
                val = float(s.sum() if aggregation == "sum" else s.mean() if aggregation == "mean" else len(s))
                return {"metric": metric_column, "aggregation": aggregation, "value": round(val, 2)}
            return {"error": "Invalid columns"}

        # Perform pandas groupby
        df[metric_column] = pd.to_numeric(df[metric_column], errors="coerce")
        grouped = df.groupby(group_by)[metric_column].agg(aggregation).reset_index()
        grouped = grouped.sort_values(by=metric_column, ascending=False).head(top_n)

        labels = [str(x) for x in grouped[group_by].tolist()]
        values = [round(float(x), 2) if not pd.isna(x) else 0.0 for x in grouped[metric_column].tolist()]

        return {
            "group_by": group_by,
            "metric": metric_column,
            "aggregation": aggregation,
            "labels": labels,
            "values": values,
            "table_data": grouped.replace({np.nan: None}).to_dict(orient="records"),
        }

    @classmethod
    def build_chart_specification(
        cls,
        file_path: str,
        chart_type: str,  # bar, line, pie, donut, horizontal_bar, area
        group_by: str,
        metric_column: str,
        aggregation: str = "sum",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        agg_result = cls.aggregate_data(file_path, group_by=group_by, metric_column=metric_column, aggregation=aggregation)

        chart_spec = {
            "chart_type": chart_type,
            "title": title or f"{aggregation.upper()} of {metric_column} by {group_by}",
            "labels": agg_result.get("labels", []),
            "datasets": [
                {
                    "name": metric_column,
                    "data": agg_result.get("values", []),
                }
            ],
            "metadata": {
                "source_file": Path(file_path).name,
                "group_by": group_by,
                "metric": metric_column,
                "aggregation": aggregation,
            }
        }
        return chart_spec


data_engine = DataAnalysisEngine()
