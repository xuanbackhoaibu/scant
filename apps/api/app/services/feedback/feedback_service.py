import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeedbackRating(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class DownvoteReason(str, Enum):
    INCORRECT = "incorrect"
    WRONG_DATA = "wrong_data"
    BAD_SOURCE = "bad_source"
    BAD_WRITING = "bad_writing"
    MISSING_INFORMATION = "missing_information"
    BAD_FORMATTING = "bad_formatting"
    OTHER = "other"


class UserFeedbackItem(BaseModel):
    feedback_id: str
    user_id: str
    report_id: Optional[str] = None
    section_id: Optional[str] = None
    rating: FeedbackRating
    downvote_reason: Optional[DownvoteReason] = None
    comment: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIUserFeedbackService:
    """Manages discreet, low-friction user feedback on AI generated content (Launch Phase L9)."""

    def __init__(self):
        self._feedbacks: List[UserFeedbackItem] = []

    def submit_feedback(
        self,
        user_id: str,
        rating: FeedbackRating,
        report_id: Optional[str] = None,
        section_id: Optional[str] = None,
        downvote_reason: Optional[DownvoteReason] = None,
        comment: Optional[str] = None,
    ) -> UserFeedbackItem:
        item = UserFeedbackItem(
            feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            report_id=report_id,
            section_id=section_id,
            rating=rating,
            downvote_reason=downvote_reason,
            comment=comment,
        )
        self._feedbacks.append(item)
        return item

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._feedbacks)
        upvotes = sum(1 for f in self._feedbacks if f.rating == FeedbackRating.THUMBS_UP)
        downvotes = sum(1 for f in self._feedbacks if f.rating == FeedbackRating.THUMBS_DOWN)

        reasons_dist: Dict[str, int] = {}
        for f in self._feedbacks:
            if f.downvote_reason:
                r_val = f.downvote_reason.value
                reasons_dist[r_val] = reasons_dist.get(r_val, 0) + 1

        satisfaction_rate = (upvotes / total * 100) if total > 0 else 100.0

        return {
            "total_feedbacks": total,
            "thumbs_up_count": upvotes,
            "thumbs_down_count": downvotes,
            "satisfaction_rate_pct": round(satisfaction_rate, 1),
            "downvote_reasons_distribution": reasons_dist,
        }


ai_feedback_service = AIUserFeedbackService()
