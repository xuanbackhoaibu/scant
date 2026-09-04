from app.services.data.data_engine import data_engine


def _profile(columns, rows):
    return {
        "file_name": "dataset.csv",
        "sheet_count": 1,
        "total_rows": len(rows),
        "total_columns": len(columns),
        "sheets": [
            {
                "name": "CSV",
                "row_count": len(rows),
                "column_count": len(columns),
                "columns": [{"name": name, "type": typ} for name, typ in columns],
                "records": rows,
            }
        ],
    }


def test_dataset_similarity_detects_same_schema_and_mostly_same_rows():
    first = _profile(
        [("Nhan vien", "text"), ("Phong ban", "text"), ("Luong co ban", "numeric")],
        [
            {"Nhan vien": "A", "Phong ban": "Kế toán", "Luong co ban": 100},
            {"Nhan vien": "B", "Phong ban": "Kinh doanh", "Luong co ban": 200},
        ],
    )
    second = _profile(
        [("Nhan vien", "text"), ("Phong ban", "text"), ("Luong co ban", "numeric")],
        [
            {"Nhan vien": "A", "Phong ban": "Kế toán", "Luong co ban": 100},
            {"Nhan vien": "B", "Phong ban": "Kinh doanh", "Luong co ban": 201},
        ],
    )

    result = data_engine.compare_dataset_profiles(first, second)

    assert result["status"] == "similar"
    assert result["similarity_score"] >= 0.9
    assert result["schema_match"] is True


def test_dataset_similarity_separates_different_structures():
    first = _profile(
        [("Nhan vien", "text"), ("Phong ban", "text"), ("Luong co ban", "numeric")],
        [{"Nhan vien": "A", "Phong ban": "Kế toán", "Luong co ban": 100}],
    )
    second = _profile(
        [("San pham", "text"), ("Doanh thu", "numeric")],
        [{"San pham": "A", "Doanh thu": 100}],
    )

    result = data_engine.compare_dataset_profiles(first, second)

    assert result["status"] == "different"
    assert result["similarity_score"] < 0.75
    assert result["schema_match"] is False
