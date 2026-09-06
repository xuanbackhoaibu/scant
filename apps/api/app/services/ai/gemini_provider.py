import json
import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.core.config import settings
from app.services.ai.base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.default_model = settings.DEFAULT_AI_MODEL or "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model

        if not self.api_key:
            if not settings.allow_ai_offline_fallback:
                raise RuntimeError("GEMINI_API_KEY is required when AI offline fallback is disabled.")
            # High-fidelity fallback generator for local offline mode / tests
            return self._mock_academic_fallback(prompt, response_format)

        url = f"{self.base_url}/{target_model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Context: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow the academic guidelines."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                candidates = data.get("candidates", [])
                if not candidates:
                    return {"text": "", "tokens_used": 0, "provider": "gemini", "model": target_model}

                candidate = candidates[0]
                content_parts = candidate.get("content", {}).get("parts", [])
                text = "".join([p.get("text", "") for p in content_parts])
                usage = data.get("usageMetadata", {})
                tokens_used = usage.get("totalTokenCount", len(text) // 4)

                return {
                    "text": text,
                    "tokens_used": tokens_used,
                    "usage": {"prompt_tokens": usage.get("promptTokenCount"), "completion_tokens": (usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0))},
                    "provider": "gemini",
                    "model": target_model,
                }
            except Exception as e:
                if not settings.allow_ai_offline_fallback:
                    raise
                # Fallback to local deterministic generator if network fails
                return self._mock_academic_fallback(prompt, response_format)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(prompt, system_prompt, model, temperature, max_tokens)
        full_text = res.get("text", "")
        # Yield in realistic stream chunks (e.g. 5-10 words per chunk)
        words = full_text.split(" ")
        chunk_size = 6
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size]) + " "
            yield chunk

    def _mock_academic_fallback(self, prompt: str, response_format: Optional[str]) -> Dict[str, Any]:
        """Offline fallback ensuring complete testability and seamless demo execution."""
        if "CHẾ ĐỘ COPILOT CHAT: ANSWER_ONLY" in prompt or "CHE DO COPILOT CHAT: ANSWER_ONLY" in prompt:
            return {
                "text": self._mock_copilot_chat_fallback(prompt),
                "is_demo": True,
                "tokens_used": 180,
                "provider": "gemini",
                "model": "gemini-2.5-flash"
            }

        if response_format == "json" or "outline" in prompt.lower():
            mock_data = {
                "project_understanding": "Đề tài tập trung vào việc nghiên cứu, phân tích, thiết kế kiến trúc hệ thống và xây dựng ứng dụng thực tế theo các chuẩn kỹ thuật chuyên nghiệp.",
                "objectives": [
                    "Nghiên cứu cơ sở lý thuyết và các công nghệ nền tảng liên quan.",
                    "Phân tích yêu cầu chức năng và phi chức năng của hệ thống.",
                    "Thiết kế kiến trúc hệ thống, cơ sở dữ liệu và các luồng xử lý chính.",
                    "Hiện thực hóa mã nguồn và tích hợp các module chức năng.",
                    "Thực nghiệm, đánh giá hiệu năng và kiểm thử toàn diện hệ thống."
                ],
                "scope": "Phạm vi đề tài bao gồm phân tích nghiệp vụ, thiết kế kiến trúc, cài đặt ứng dụng và kiểm thử tính năng hoàn chỉnh.",
                "suggested_methodology": "Áp dụng phương pháp nghiên cứu kết hợp thực nghiệm (Experimental Research) và mô hình phát triển phần mềm lặp Agile/Scrum.",
                "outline": [
                    {
                        "title": "LỜI MỞ ĐẦU",
                        "level": 1,
                        "position": 1,
                        "section_number": "",
                        "description": "Giới thiệu bối cảnh, tính cấp thiết và lý do chọn đề tài.",
                        "children": []
                    },
                    {
                        "title": "CHƯƠNG 1: TỔNG QUAN VỀ ĐỀ TÀI",
                        "level": 1,
                        "position": 2,
                        "section_number": "1",
                        "description": "Bối cảnh, mục tiêu, đối tượng, phạm vi nghiên cứu và phương pháp thực hiện.",
                        "children": [
                            {"title": "1.1 Bối cảnh và lý do chọn đề tài", "level": 2, "position": 1, "section_number": "1.1", "description": "", "children": []},
                            {"title": "1.2 Mục tiêu nghiên cứu", "level": 2, "position": 2, "section_number": "1.2", "description": "", "children": []},
                            {"title": "1.3 Phạm vi và đối tượng nghiên cứu", "level": 2, "position": 3, "section_number": "1.3", "description": "", "children": []},
                            {"title": "1.4 Phương pháp thực hiện và cấu trúc báo cáo", "level": 2, "position": 4, "section_number": "1.4", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG",
                        "level": 1,
                        "position": 3,
                        "section_number": "2",
                        "description": "Trình bày các framework, kiến trúc và công nghệ cốt lõi.",
                        "children": [
                            {"title": "2.1 Tổng quan về kiến trúc nền tảng", "level": 2, "position": 1, "section_number": "2.1", "description": "", "children": []},
                            {"title": "2.2 Các công nghệ và thư viện chủ chốt", "level": 2, "position": 2, "section_number": "2.2", "description": "", "children": []},
                            {"title": "2.3 Cơ chế xác thực và bảo mật", "level": 2, "position": 3, "section_number": "2.3", "description": "", "children": []},
                            {"title": "2.4 So sánh và đánh giá các giải pháp công nghệ", "level": 2, "position": 4, "section_number": "2.4", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG",
                        "level": 1,
                        "position": 4,
                        "section_number": "3",
                        "description": "Đặc tả yêu cầu, Use Case, thiết kế cơ sở dữ liệu và kiến trúc.",
                        "children": [
                            {"title": "3.1 Phân tích yêu cầu chức năng và phi chức năng", "level": 2, "position": 1, "section_number": "3.1", "description": "", "children": []},
                            {"title": "3.2 Thiết kế sơ đồ Use Case và luồng nghiệp vụ", "level": 2, "position": 2, "section_number": "3.2", "description": "", "children": []},
                            {"title": "3.3 Thiết kế cơ sở dữ liệu và lược đồ quan hệ (ERD)", "level": 2, "position": 3, "section_number": "3.3", "description": "", "children": []},
                            {"title": "3.4 Thiết kế kiến trúc phần mềm và tương tác module", "level": 2, "position": 4, "section_number": "3.4", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "CHƯƠNG 4: HIỆN THỰC HÓA VÀ KẾT QUẢ TRIỂN KHAI",
                        "level": 1,
                        "position": 5,
                        "section_number": "4",
                        "description": "Chi tiết triển khai mã nguồn, giao diện và các tính năng chính.",
                        "children": [
                            {"title": "4.1 Triển khai cấu trúc module và dịch vụ lõi", "level": 2, "position": 1, "section_number": "4.1", "description": "", "children": []},
                            {"title": "4.2 Hiện thực hóa các tính năng nghiệp vụ chính", "level": 2, "position": 2, "section_number": "4.2", "description": "", "children": []},
                            {"title": "4.3 Giao diện người dùng và trải nghiệm tương tác", "level": 2, "position": 3, "section_number": "4.3", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "CHƯƠNG 5: KIỂM THỬ VÀ ĐÁNH GIÁ KẾT QUẢ",
                        "level": 1,
                        "position": 6,
                        "section_number": "5",
                        "description": "Kế hoạch kiểm thử, kết quả kiểm thử chức năng và hiệu năng.",
                        "children": [
                            {"title": "5.1 Môi trường và kịch bản kiểm thử", "level": 2, "position": 1, "section_number": "5.1", "description": "", "children": []},
                            {"title": "5.2 Kết quả kiểm thử chức năng và phi chức năng", "level": 2, "position": 2, "section_number": "5.2", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN",
                        "level": 1,
                        "position": 7,
                        "section_number": "6",
                        "description": "Tổng kết kết quả đạt được, hạn chế và định hướng phát triển tương lai.",
                        "children": [
                            {"title": "6.1 Các kết quả đạt được của đề tài", "level": 2, "position": 1, "section_number": "6.1", "description": "", "children": []},
                            {"title": "6.2 Hạn chế và hướng phát triển mở rộng", "level": 2, "position": 2, "section_number": "6.2", "description": "", "children": []}
                        ]
                    },
                    {
                        "title": "TÀI LIỆU THAM KHẢO",
                        "level": 1,
                        "position": 8,
                        "section_number": "",
                        "description": "Danh mục các tài liệu và bài báo khoa học được trích dẫn theo chuẩn IEEE.",
                        "children": []
                    }
                ]
            }
            return {
                "text": json.dumps(mock_data, ensure_ascii=False, indent=2),
                "is_demo": True,
                "tokens_used": 650,
                "provider": "gemini",
                "model": "gemini-2.5-flash"
            }

        return {
            "text": self._mock_section_fallback(prompt),
            "is_demo": True,
                "tokens_used": 1800,
            "provider": "gemini",
            "model": "gemini-2.5-flash"
        }

    def _mock_section_fallback(self, prompt: str) -> str:
        """Generate a usable long-form section when the live Gemini API is unavailable."""
        section_title = "Mục báo cáo"
        topic_name = "đề tài nghiên cứu"

        for marker in ["MỤC ĐANG SOẠN THẢO:", "MUC DANG SOAN THAO:"]:
            if marker in prompt:
                section_title = prompt.split(marker, 1)[1].splitlines()[0].strip()
                section_title = section_title.split("(Cấp độ", 1)[0].strip()
                break

        for marker in ["ĐỀ TÀI BÁO CÁO:", "DE TAI BAO CAO:"]:
            if marker in prompt:
                topic_name = prompt.split(marker, 1)[1].splitlines()[0].strip()
                break

        target_words = 900
        lowered = prompt.lower()
        for unit in ["từ", "tu"]:
            if unit in lowered:
                import re
                match = re.search(r"(\d{3,5})\s*(?:từ|tu)", lowered)
                if match:
                    target_words = max(700, min(int(match.group(1)), 1800))
                    break

        return self._mock_section_text(section_title, topic_name, target_words)

    def _mock_section_text(self, section_title: str, topic_name: str, target_words: int) -> str:
        title = section_title.strip() or "Mục báo cáo"
        topic = " ".join((topic_name or "đề tài nghiên cứu").split()).strip()
        upper = title.upper()
        stripped = __import__("re").sub(r"^\d+(?:\.\d+){1,2}\s*", "", title).strip()
        if stripped != title:
            specific = self._mock_numbered_section_text(title, stripped, topic)
            if specific:
                return specific

        if upper.startswith("LỜI"):
            paragraphs = [
                f"Đề tài \"{topic}\" được thực hiện nhằm hệ thống hóa kiến thức nền tảng và làm rõ cách các thành phần kỹ thuật phối hợp trong một hệ thống hoàn chỉnh.",
                "Báo cáo tiếp cận vấn đề theo hướng học thuật kết hợp thực tiễn: trình bày cơ sở lý thuyết, phân tích yêu cầu, mô tả thiết kế, triển khai và đánh giá kết quả.",
                "Nội dung được tổ chức để người đọc có thể theo dõi từ bối cảnh hình thành đề tài đến kết quả đạt được, đồng thời nhận diện các hạn chế còn cần tiếp tục cải thiện.",
            ]
        elif "TỔNG QUAN" in upper or "BỐI CẢNH" in upper:
            paragraphs = [
                f"Chương tổng quan đặt nền tảng cho đề tài \"{topic}\" bằng cách xác định lý do chọn đề tài, mục tiêu nghiên cứu, phạm vi thực hiện và phương pháp tiếp cận.",
                "Trọng tâm của chương là làm rõ vấn đề cần giải quyết, đối tượng được khảo sát và giá trị thực tiễn của kết quả nghiên cứu.",
                "| Nội dung | Vai trò |\n|---|---|\n| Bối cảnh | Giải thích nhu cầu nghiên cứu |\n| Mục tiêu | Xác định kết quả cần đạt |\n| Phạm vi | Giới hạn nội dung triển khai |",
            ]
        elif "CƠ SỞ" in upper or "LÝ THUYẾT" in upper or "CÔNG NGHỆ" in upper:
            paragraphs = [
                "Chương này trình bày các khái niệm và công nghệ nền tảng phục vụ quá trình phân tích và triển khai hệ thống.",
                "Các thành phần như bộ xử lý, bộ nhớ, lưu trữ, mạng, hệ điều hành và phần mềm ứng dụng cần được xem xét trong quan hệ tương tác thay vì tách rời.",
                "| Thành phần | Vai trò | Tác động |\n|---|---|---|\n| CPU | Xử lý tính toán | Ảnh hưởng tốc độ thực thi |\n| RAM | Lưu dữ liệu tạm | Ảnh hưởng độ trễ |\n| Mạng | Truyền thông | Ảnh hưởng thông lượng |",
            ]
        elif "PHÂN TÍCH" in upper or "THIẾT KẾ" in upper or "YÊU CẦU" in upper:
            paragraphs = [
                "Phần phân tích và thiết kế chuyển mục tiêu nghiên cứu thành yêu cầu cụ thể, từ đó xây dựng mô hình hệ thống có thể triển khai.",
                "Cần phân biệt yêu cầu chức năng với yêu cầu phi chức năng như hiệu năng, bảo mật, độ tin cậy và khả năng mở rộng.",
                "[[IMAGE:title=Sơ đồ thiết kế hệ thống;prompt=Sơ đồ kiến trúc gồm giao diện, API, cơ sở dữ liệu, lưu trữ và giám sát]]",
            ]
        elif "TRIỂN KHAI" in upper or "CÀI ĐẶT" in upper or "CẤU HÌNH" in upper:
            paragraphs = [
                "Phần triển khai mô tả các bước chuẩn bị môi trường, cài đặt phần mềm, cấu hình dịch vụ và đưa hệ thống vào trạng thái vận hành.",
                "Một quy trình triển khai tốt cần có kiểm tra sau cài đặt, ghi log, sao lưu cấu hình và phương án phục hồi khi dịch vụ gặp sự cố.",
                "| Giai đoạn | Kết quả cần đạt |\n|---|---|\n| Chuẩn bị | Môi trường sẵn sàng |\n| Cấu hình | Dịch vụ chạy đúng |\n| Kiểm tra | Xác nhận hệ thống hoạt động |",
            ]
        elif "KIỂM THỬ" in upper or "ĐÁNH GIÁ" in upper or "HIỆU NĂNG" in upper:
            paragraphs = [
                "Phần kiểm thử đánh giá mức độ đáp ứng của hệ thống so với yêu cầu ban đầu thông qua các tiêu chí có thể đo lường.",
                "Các chỉ số quan trọng gồm thời gian phản hồi, thông lượng, mức sử dụng tài nguyên, tỷ lệ lỗi và khả năng phục hồi.",
                "[[CHART:type=bar;title=Mức đáp ứng tiêu chí kiểm thử;labels=Chức năng,Hiệu năng,Bảo mật,Ổn định;values=88,80,76,84;unit=%]]",
            ]
        elif "KẾT LUẬN" in upper:
            paragraphs = [
                f"Báo cáo đã hoàn thành việc phân tích các nội dung trọng tâm của đề tài \"{topic}\" và chỉ ra mối quan hệ giữa cơ sở lý thuyết, thiết kế, triển khai và đánh giá.",
                "Kết quả cho thấy chất lượng hệ thống phụ thuộc vào sự cân bằng giữa kiến trúc, cấu hình, tài nguyên, bảo mật và quy trình vận hành.",
                "Hướng phát triển tiếp theo là bổ sung thêm dữ liệu đo kiểm, mở rộng kịch bản thử nghiệm và tối ưu các điểm còn hạn chế.",
            ]
        else:
            paragraphs = [
                f"Mục \"{title}\" làm rõ một nội dung cụ thể trong đề tài \"{topic}\" và cần được trình bày theo đúng vai trò của nó trong cấu trúc báo cáo.",
                "Nội dung nên đi từ khái niệm đến phân tích, sau đó liên hệ với điều kiện triển khai hoặc minh chứng thực tế.",
                "Cách trình bày này giúp báo cáo mạch lạc hơn và tránh lặp lại nguyên văn các chương mục khác.",
            ]

        text = f"{title}\n\n" + "\n\n".join(paragraphs)
        additions = [
            "Về mặt thực tiễn, nội dung cần được gắn với điều kiện sử dụng cụ thể để các nhận xét có giá trị áp dụng.",
            "Về mặt kỹ thuật, mỗi lựa chọn cần được đánh giá theo hiệu năng, chi phí, độ ổn định và khả năng mở rộng.",
            "Về mặt trình bày, phần này cần kết thúc bằng nhận định rõ để liên kết với phần tiếp theo của báo cáo.",
        ]
        i = 0
        while len(text.split()) < target_words and i < len(additions) * 3:
            text += "\n\n" + additions[i % len(additions)]
            i += 1
        return text

    def _mock_numbered_section_text(self, title: str, stripped_title: str, topic: str) -> str:
        upper = stripped_title.upper()
        topic_lower = topic.lower()
        is_arm_x86 = "arm" in topic_lower and "x86" in topic_lower

        if "MỤC TIÊU" in upper:
            return (
                f"{title}\n\n"
                f"Mục tiêu của đề tài \"{topic}\" là làm rõ sự khác biệt giữa các kiến trúc xử lý ở cả góc độ nguyên lý và ứng dụng thực tế. Nội dung không chỉ nêu khái niệm mà còn xác định các tiêu chí đánh giá có thể sử dụng khi lựa chọn nền tảng cho một hệ thống máy tính hiện đại.\n\n"
                "Các mục tiêu cụ thể gồm: phân tích đặc điểm kiến trúc, đánh giá hiệu năng, xem xét mức tiêu thụ năng lượng, so sánh khả năng tương thích phần mềm và nhận diện bối cảnh ứng dụng phù hợp. Nhờ đó, báo cáo có thể đưa ra nhận xét có căn cứ thay vì kết luận cảm tính.\n\n"
                "| Nhóm mục tiêu | Nội dung cần đạt |\n|---|---|\n| Kiến thức | Hiểu nguyên lý kiến trúc và tổ chức xử lý |\n| So sánh | Đánh giá theo hiệu năng, điện năng và tương thích |\n| Ứng dụng | Đề xuất bối cảnh sử dụng phù hợp |\n\n"
                "Kết quả mong muốn là người đọc hiểu vì sao cùng là bộ xử lý nhưng ARM và x86 có lợi thế khác nhau trong từng môi trường như máy tính cá nhân, thiết bị di động, hệ thống nhúng, máy chủ và nền tảng điện toán đám mây."
            )
        if "PHẠM VI" in upper or "ĐỐI TƯỢNG" in upper:
            arm_detail = "Với ARM, báo cáo chú ý đến thiết kế tiết kiệm năng lượng, SoC và xu hướng mở rộng sang laptop/máy chủ. Với x86, báo cáo tập trung vào hiệu năng truyền thống, khả năng tương thích và hệ sinh thái phần mềm lâu đời." if is_arm_x86 else "Báo cáo tập trung vào các thành phần và tiêu chí có ảnh hưởng trực tiếp đến quá trình thiết kế, triển khai và đánh giá hệ thống."
            return (
                f"{title}\n\n"
                f"Phạm vi nghiên cứu của mục này được giới hạn trong các yếu tố có liên quan trực tiếp đến đề tài \"{topic}\". Nội dung xem xét khía cạnh kiến trúc, môi trường vận hành, phần mềm hỗ trợ, tiêu chí hiệu năng và điều kiện triển khai trong thực tế.\n\n"
                f"{arm_detail}\n\n"
                "| Nội dung | Phạm vi xem xét |\n|---|---|\n| Kiến trúc | Tập lệnh, tổ chức xử lý, bộ nhớ và cache |\n| Hệ thống | Máy tính cá nhân, máy chủ, thiết bị nhúng và cloud |\n| Giới hạn | Không đi sâu vào thiết kế transistor hoặc benchmark ngoài phạm vi môn học |\n\n"
                "Việc xác định rõ phạm vi giúp các chương sau có trọng tâm hơn. Các nhận xét được đặt trong điều kiện sử dụng phổ biến, không khẳng định tuyệt đối cho mọi dòng phần cứng hoặc mọi nhà sản xuất."
            )
        if "PHƯƠNG PHÁP" in upper or "CẤU TRÚC" in upper:
            return (
                f"{title}\n\n"
                "Phương pháp thực hiện được xây dựng theo hướng tổng hợp tài liệu, phân tích kiến trúc và so sánh theo tiêu chí. Trước hết, báo cáo hệ thống hóa các khái niệm nền tảng để tạo cơ sở chung cho việc đánh giá.\n\n"
                "Sau đó, từng tiêu chí như hiệu năng, điện năng, khả năng tương thích, chi phí và khả năng mở rộng được sử dụng để phân tích. Cách tiếp cận này giúp nội dung giữ được sự cân bằng giữa lý thuyết và ứng dụng.\n\n"
                "Cấu trúc báo cáo đi từ tổng quan đến cơ sở lý thuyết, từ phân tích so sánh đến đánh giá và kết luận. Trình tự này giúp người đọc theo dõi được mạch lập luận và thấy rõ cơ sở của từng nhận xét."
            )
        if "BỐI CẢNH" in upper or "LÝ DO" in upper:
            return (
                f"{title}\n\n"
                f"Bối cảnh nghiên cứu của đề tài \"{topic}\" xuất phát từ sự thay đổi nhanh của hệ thống máy tính hiện đại. Các nền tảng phần cứng ngày nay không chỉ cạnh tranh về tốc độ xử lý mà còn về điện năng, khả năng tích hợp, độ ổn định và hệ sinh thái phần mềm.\n\n"
                "Trong bối cảnh đó, việc hiểu rõ đặc điểm của từng kiến trúc giúp người học có cơ sở lựa chọn giải pháp phù hợp. Một kiến trúc mạnh trong máy chủ truyền thống chưa chắc tối ưu cho thiết bị tiết kiệm điện, và một kiến trúc tiết kiệm năng lượng cũng cần được đánh giá về khả năng tương thích phần mềm.\n\n"
                "Vì vậy, đề tài có ý nghĩa cả về mặt học thuật lẫn thực tiễn, đặc biệt khi các xu hướng như cloud, edge computing, thiết bị di động và máy tính cá nhân hiệu năng cao đang phát triển song song."
            )
        return None

    def _mock_copilot_chat_fallback(self, prompt: str) -> str:
        question = ""
        if "CÂU HỎI CỦA NGƯỜI DÙNG:" in prompt:
            question = prompt.split("CÂU HỎI CỦA NGƯỜI DÙNG:", 1)[1].split("NGỮ CẢNH DỰ ÁN:", 1)[0].strip().strip('"')
        project_topic = ""
        for line in prompt.splitlines():
            if line.startswith("- Đề tài/dự án:"):
                project_topic = line.split(":", 1)[1].strip()
                break

        lowered = question.lower()
        if any(term in lowered for term in ["đề tài", "chủ đề", "tên báo cáo", "tôi đang làm"]):
            return f"Đề tài hiện tại của bạn là: **{project_topic or 'chưa có tên đề tài trong dữ liệu dự án'}**."
        if any(term in lowered for term in ["tác dụng", "để làm gì", "là gì"]):
            return "Phần này dùng để hỗ trợ bạn hỏi đáp về dự án và điều khiển AI viết/sửa nội dung khi có yêu cầu rõ ràng."
        if any(term in lowered for term in ["không hoạt động", "lỗi", "sao"]):
            return "Có thể chức năng đang thiếu dữ liệu ngữ cảnh hoặc chưa nhận đúng ý định. Bạn mô tả thao tác cụ thể, mình sẽ kiểm tra đúng phần đó."
        return "Mình hiểu. Bạn có thể hỏi trực tiếp về dự án, nội dung đang chọn, hoặc yêu cầu rõ nếu muốn mình viết/sửa/chèn vào tài liệu."
