import json
from status_tools import StatusTools

tools = StatusTools(mode="snapshot")

# Bước 1: tìm incident liên quan đến purge.
status = tools.get_status("cloudflare", "purge")
print("=== KET QUA TIM KIEM ===")
print(json.dumps(status, ensure_ascii=False, indent=2))

# Bước 2: lấy ID từ kết quả rồi đọc chi tiết.
if status["incidents"]:
    incident_id = status["incidents"][0]["id"]
    details = tools.get_incident_details("cloudflare", incident_id)
    print("\n=== CHI TIET INCIDENT ===")
    print(json.dumps(details, ensure_ascii=False, indent=2))
else:
    print("Khong tim thay trong pham vi tim kiem.")

# Bước 3: so sánh cùng ý nghĩa nhưng từ khóa tiếng Việt.
other = tools.get_status("cloudflare", "xóa bộ nhớ đệm")
print("\nSo incident khop tu khoa tieng Viet:",
      other["matching_incidents_in_last_50"])