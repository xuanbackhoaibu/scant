from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    DIAGRAM = "diagram"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    LIST = "list"
    FORMULA = "formula"


class BoundingBox(BaseModel):
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0


class LayoutBlock(BaseModel):
    block_id: str
    block_type: BlockType
    page_number: int
    reading_order: int
    bounding_box: BoundingBox = Field(default_factory=BoundingBox)
    text_content: str = ""
    style: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    structured_data: Optional[Dict[str, Any]] = None  # e.g., table cells, chart metrics
    visual_description: Optional[str] = None  # AI visual interpretation of chart/image/diagram
    needs_review: bool = False  # Flagged if confidence < 0.70


class DocumentPage(BaseModel):
    page_number: int
    width: float = 612.0  # standard US Letter / A4 points
    height: float = 792.0
    blocks: List[LayoutBlock] = Field(default_factory=list)
    has_visual_elements: bool = False


class DocumentIntelligenceTree(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    pages: List[DocumentPage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary_text: str = ""
    table_of_contents: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_tables_count: int = 0
    extracted_visuals_count: int = 0
