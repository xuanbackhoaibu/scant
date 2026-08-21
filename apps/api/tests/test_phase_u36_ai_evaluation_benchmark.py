import pytest
from app.services.benchmarks.benchmark_engine import (
    benchmark_engine,
    BenchmarkTestCase,
    BenchmarkReport,
)


def test_ai_benchmark_scoring():
    tc = BenchmarkTestCase(
        test_id="tc_sample_01",
        category="data_report",
        prompt="Báo cáo kết quả kinh doanh quý 2 tăng trưởng 24% đạt 450 tỷ.",
        expected_keywords=["doanh thu", "24%", "450 tỷ"],
        ground_truth_numeric_values=[24.0, 450.0],
    )

    # 1. High-quality output matching keywords and numbers
    good_output = "Tổng hợp doanh thu quý 2 tăng trưởng 24% với doanh thu thuần đạt 450 tỷ VNĐ."
    score = benchmark_engine.evaluate_output(tc, good_output)

    assert score.passed is True
    assert score.factual_accuracy >= 0.80
    assert score.numeric_accuracy == 1.0
    assert score.unsupported_claim_rate == 0.0

    # 2. Inaccurate output missing numbers
    bad_output = "Báo cáo chung chung không có số liệu cụ thể."
    bad_score = benchmark_engine.evaluate_output(tc, bad_output)
    assert bad_score.passed is False
    assert bad_score.numeric_accuracy == 0.0


def test_full_benchmark_regression_suite():
    report = benchmark_engine.run_benchmark_suite()

    assert isinstance(report, BenchmarkReport)
    assert report.total_test_cases >= 6
    assert report.passed_test_cases >= 5
    assert report.overall_quality_score_pct >= 85.0
    assert len(report.category_breakdown) >= 6
