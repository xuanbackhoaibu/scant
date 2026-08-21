import hashlib
from typing import Any, Dict, List, Optional


class SmartMappingService:
    """
    Smart Mapping Memory (Phase U17).
    Learns and reuses canonical field mappings across datasets based on schema fingerprints.
    """

    # Canonical Business Synonyms
    CANONICAL_SYNONYMS = {
        "revenue": ["revenue", "sales", "doanh thu", "sales amount", "total revenue", "turnover", "tong doanh thu", "tổng doanh thu"],
        "cost": ["cost", "expense", "chi phi", "chi phí", "gia von", "giá vốn", "cogs", "total cost", "tong chi phi", "tổng chi phí"],
        "profit": ["profit", "net income", "loi nhuan", "lợi nhuận", "loi nhuan thuan", "lợi nhuận thuần", "ebitda", "gross profit"],
        "customer": ["customer", "client", "khach hang", "khách hàng", "user", "account"],
        "date": ["date", "time", "ngay", "ngày", "thang", "tháng", "year", "nam", "năm", "period", "ky", "kỳ"],
        "quantity": ["quantity", "volume", "so luong", "số lượng", "san luong", "sản lượng", "units", "so luong ban"],
        "region": ["region", "area", "khu vuc", "khu vực", "vung mien", "vùng miền", "location", "dia ban", "địa bàn"],
    }

    def __init__(self):
        # In-memory mapping profile storage (schema_fingerprint -> mapping)
        self._profiles: Dict[str, Dict[str, str]] = {}

    def compute_fingerprint(self, column_names: List[str]) -> str:
        """Computes deterministic hash from sorted normalized column names."""
        normalized = sorted([c.strip().lower() for c in column_names])
        raw_str = "|".join(normalized)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]

    def infer_canonical_mapping(self, column_names: List[str]) -> Dict[str, str]:
        """Maps dataset column names to canonical standard names."""
        fingerprint = self.compute_fingerprint(column_names)
        if fingerprint in self._profiles:
            return self._profiles[fingerprint]

        mapping: Dict[str, str] = {}
        for col in column_names:
            col_clean = col.strip().lower()
            matched_canonical = None
            for canonical, syns in self.CANONICAL_SYNONYMS.items():
                if any(syn in col_clean or col_clean in syn for syn in syns):
                    matched_canonical = canonical
                    break
            mapping[col] = matched_canonical or col_clean

        # Save to memory profile
        self._profiles[fingerprint] = mapping
        return mapping

    def save_custom_mapping(self, column_names: List[str], mapping: Dict[str, str]) -> str:
        fingerprint = self.compute_fingerprint(column_names)
        self._profiles[fingerprint] = mapping
        return fingerprint


smart_mapping_service = SmartMappingService()
