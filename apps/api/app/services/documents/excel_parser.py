import os
from typing import Any, Dict, List, Optional
import pandas as pd


class ExcelParser:
    """Parser for Excel and CSV datasets."""

    @staticmethod
    def parse_dataset(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        row_count, col_count = df.shape
        columns_info: List[Dict[str, Any]] = []

        for col in df.columns:
            series = df[col]
            dtype_str = str(series.dtype)
            is_numeric = pd.api.types.is_numeric_dtype(series)

            stats = {
                "null_count": int(series.isnull().sum()),
                "unique_count": int(series.nunique()),
            }

            if is_numeric:
                clean_s = series.dropna()
                if len(clean_s) > 0:
                    stats["min"] = float(clean_s.min())
                    stats["max"] = float(clean_s.max())
                    stats["mean"] = float(clean_s.mean())

            sample_vals = [str(x) for x in series.dropna().head(5).tolist()]

            columns_info.append({
                "name": str(col),
                "data_type": "number" if is_numeric else "string",
                "is_numeric": is_numeric,
                "stats": stats,
                "sample_values": sample_vals
            })

        preview_rows = df.head(10).fillna("").to_dict(orient="records")

        return {
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns_info,
            "preview_rows": preview_rows,
        }


excel_parser = ExcelParser()
