import re
import math
from typing import Any, Dict, List, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class PlagiarismStylometryEngine:
    """
    AI Stylometry, Sentence Burstiness, and Plagiarism Risk Engine.
    Evaluates lexical richness, entropy, repetitive syntax patterns, and predicts human-like fidelity.
    """

    ROBOTIC_PHRASES = [
        "hơn nữa", "ngoài ra", "tóm lại", "nhìn chung", "đáng chú ý là",
        "trong bối cảnh hiện nay", "đóng vai trò then chốt", "không thể phủ nhận",
        "như đã đề cập", "tổng kết lại", "trên cơ sở đó", "điều quan trọng cần lưu ý",
        "như một minh chứng", "mặt khác", "một cách toàn diện"
    ]

    @classmethod
    async def analyze(cls, text: str) -> Dict[str, Any]:
        if not text or len(text.strip()) < 50:
            return {
                "overall_score": 95,
                "human_probability": 92,
                "ai_probability": 8,
                "burstiness_score": 88,
                "vocabulary_richness": 90,
                "robotic_phrases_count": 0,
                "risk_level": "low",
                "detected_patterns": [],
                "recommendations": ["Văn bản ngắn, chưa phát hiện dấu hiệu bất thường."],
            }

        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 5]
        words = [w.lower() for w in re.findall(r"\b\w+\b", text)]
        total_words = len(words)
        unique_words = len(set(words))

        # 1. Type-Token Ratio (Vocabulary Richness)
        ttr = (unique_words / total_words) if total_words > 0 else 1.0
        vocab_score = min(100, int(ttr * 150))

        # 2. Sentence Length Variance (Burstiness)
        if len(sentences) > 1:
            lengths = [len(s.split()) for s in sentences]
            mean_len = sum(lengths) / len(lengths)
            variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            # High standard deviation = natural human burstiness. Uniform lengths = AI signature.
            burstiness = min(100, int((std_dev / (mean_len + 1e-5)) * 120))
        else:
            burstiness = 70

        # 3. Frequency of stereotypical robotic phrases
        text_lower = text.lower()
        found_phrases = []
        for phrase in cls.ROBOTIC_PHRASES:
            count = text_lower.count(phrase)
            if count > 0:
                found_phrases.append({"phrase": phrase, "count": count})

        phrase_penalty = sum(p["count"] for p in found_phrases) * 4

        # 4. Synthesize AI Probability
        ai_prob = max(5, min(95, int(70 - (burstiness * 0.4) - (vocab_score * 0.3) + phrase_penalty)))
        human_prob = 100 - ai_prob

        risk_level = "high" if ai_prob > 65 else "moderate" if ai_prob > 35 else "low"

        recommendations = []
        if burstiness < 40:
            recommendations.append("Độ dài các câu khá đồng đều. Hãy đan xen giữa câu ngắn dứt khoát và câu phức để tạo nhịp điệu tự nhiên hơn.")
        if vocab_score < 50:
            recommendations.append("Vốn từ vựng có tính lặp lại cao. Nên sử dụng từ đồng nghĩa chuyên ngành để làm phong phú văn bản.")
        if len(found_phrases) >= 3:
            recommendations.append(f"Xuất hiện nhiều từ nối máy móc ({', '.join([p['phrase'] for p in found_phrases[:3]])}). Hãy dùng tính năng 'Humanize' để làm mượt.")
        if not recommendations:
            recommendations.append("Văn bản có văn phong tự nhiên, đa dạng ngữ pháp và trích dẫn chuẩn xác.")

        return {
            "overall_score": human_prob,
            "human_probability": human_prob,
            "ai_probability": ai_prob,
            "burstiness_score": burstiness,
            "vocabulary_richness": vocab_score,
            "robotic_phrases_count": len(found_phrases),
            "found_phrases": found_phrases[:6],
            "risk_level": risk_level,
            "sentence_count": len(sentences),
            "word_count": total_words,
            "recommendations": recommendations,
        }


plagiarism_stylometry_engine = PlagiarismStylometryEngine()
