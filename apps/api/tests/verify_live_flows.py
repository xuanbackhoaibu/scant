import httpx
import openpyxl
import tempfile
import os

API_BASE = "http://127.0.0.1:8050/api/v1/data"

def create_test_file():
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "Bang_luong"
    ws1.append(["Mã NV", "Họ tên", "Phòng ban", "Lương cơ bản", "Thực lĩnh"])
    ws1.append(["NV001", "Nguyễn Văn A", "Kinh doanh", 12000000, 15500000])
    ws1.append(["NV002", "Trần Thị B", "Kỹ thuật", 18000000, 22000000])
    ws1.append(["NV003", "Lê Văn C", "Kinh doanh", 10000000, 11500000])
    ws1.append(["NV004", "Phạm Thị D", "Nhân sự", 14000000, 16000000])
    ws1.append(["NV005", "Hoàng Văn E", "Kỹ thuật", 18000000, 22000000])

    ws2 = wb.create_sheet(title="Tong_hop")
    ws2.append(["Phòng ban", "Số nhân sự", "Tổng quỹ lương"])
    ws2.append(["Kinh doanh", 2, 27000000])
    ws2.append(["Kỹ thuật", 2, 44000000])
    ws2.append(["Nhân sự", 1, 16000000])

    wb.save(path)
    wb.close()
    return path

def run_verifications():
    path = create_test_file()
    print("=== LIVE END-TO-END FLOW VERIFICATION ===")

    # Flow 1: Preview Upload & Full Scanner
    with open(path, "rb") as f:
        res = httpx.post(
            f"{API_BASE}/preview-upload",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=30.0,
        )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert data["sheet_count"] == 2
    assert "workbook_context" in data
    assert data["workbook_context"]["sheetCount"] == 2
    print("✓ Flow 1 (Upload & Full Workbook Scanner) PASSED")

    # Flow 2: FIND_MAX ("nhân viên thực lĩnh cao nhất")
    with open(path, "rb") as f:
        res2 = httpx.post(
            f"{API_BASE}/workbook-analysis-action",
            data={"prompt": "nhân viên thực lĩnh cao nhất", "sheet_name": "Bang_luong"},
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=30.0,
        )
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["ok"] is True
    assert data2["mode"] == "analysis_action"
    assert "22.000.000" in data2["answer"]
    assert data2["evidence"]["operation"] == "MAX"
    print("✓ Flow 2 (Analysis Action: FIND_MAX) PASSED")

    # Flow 3: SUM ("tổng thực lĩnh")
    with open(path, "rb") as f:
        res3 = httpx.post(
            f"{API_BASE}/workbook-analysis-action",
            data={"prompt": "tổng thực lĩnh", "sheet_name": "Bang_luong"},
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=30.0,
        )
    assert res3.status_code == 200, res3.text
    data3 = res3.json()
    assert data3["ok"] is True
    assert "87.000.000" in data3["answer"]
    assert data3["evidence"]["operation"] == "SUM"
    print("✓ Flow 3 (Analysis Action: SUM) PASSED")

    # Flow 4: FIND_DUPLICATES ("tìm dữ liệu trùng và tô vàng")
    with open(path, "rb") as f:
        res4 = httpx.post(
            f"{API_BASE}/workbook-analysis-action",
            data={"prompt": "tìm dữ liệu trùng và tô vàng", "sheet_name": "Bang_luong", "highlight_color": "#FEF08A"},
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=30.0,
        )
    assert res4.status_code == 200, res4.text
    data4 = res4.json()
    assert data4["ok"] is True
    assert data4["result_type"] == "duplicate"
    print("✓ Flow 4 (Analysis Action: FIND_DUPLICATES) PASSED")

    # Flow 5: Chat Isolation ("File này có bao nhiêu sheet?")
    with open(path, "rb") as f:
        res5 = httpx.post(
            f"{API_BASE}/workbook-chat",
            data={"message": "File này có bao nhiêu sheet?", "sheet_name": "Bang_luong"},
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=30.0,
        )
    assert res5.status_code == 200, res5.text
    data5 = res5.json()
    assert data5["ok"] is True
    assert data5["intent"] == "WORKBOOK_QUESTION"
    assert "2 sheet" in data5["answer"]
    print("✓ Flow 5 (Chat Flow & Smalltalk Isolation) PASSED")

    # Flow 6: Action Undo
    res6 = httpx.post(f"{API_BASE}/action-undo", data={"session_id": "test_session"}, timeout=30.0)
    assert res6.status_code == 200, res6.text
    print("✓ Flow 6 (Action Engine Undo) PASSED")

    # Flow 7: Cross File Compare
    with open(path, "rb") as f1, open(path, "rb") as f2:
        res7 = httpx.post(
            f"{API_BASE}/cross-file-compare",
            data={"sheet1_name": "Bang_luong", "sheet2_name": "Bang_luong", "key_column_1": "Mã NV", "key_column_2": "Mã NV"},
            files={
                "file_1": ("file1.xlsx", f1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                "file_2": ("file2.xlsx", f2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            },
            timeout=30.0,
        )
    assert res7.status_code == 200, res7.text
    data7 = res7.json()
    assert data7["ok"] is True
    assert data7["operation"] == "CROSS_FILE_COMPARE"
    assert data7["total_keys"] == 5
    print("✓ Flow 7 (Cross File Compare API) PASSED")

    os.remove(path)
    print("\nALL 6 FLOWS VERIFIED 100% SUCCESSFULLY AGAINST LIVE SERVICE!")

if __name__ == "__main__":
    run_verifications()
