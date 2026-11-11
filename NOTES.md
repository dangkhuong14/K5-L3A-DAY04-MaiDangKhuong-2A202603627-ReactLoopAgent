# Ghi chú phân tích · Day 04

Họ và tên: Mai Đăng Khương
MSSV: 2A202603627

## 1. Case được chọn

- ID case: H6.
- Câu trả lời của agent (trích): “Incident này không nêu rõ nguyên nhân gốc rễ của lỗi mà chỉ mô tả tình trạng và ảnh hưởng.”
- Điểm ở lần chạy 1: 60/100.

## 2. Bằng chứng trong trace

Trích các trường liên quan từ trace H6 trong `eval_before.json`:

```json
[
  {
    "event": "tool",
    "step": 1,
    "name": "get_incident_details",
    "arguments": {"provider": "github", "incident_id": "h02n9572mx9y"},
    "result": {
      "updates": [
        {"body": "Please refer to the combined summary in this related incident: https://www.githubstatus.com/incidents/xr3myzj7ms51"}
      ]
    }
  },
  {"event": "model", "step": 2, "finish": "stop", "tool_calls": 0}
]
```

Agent nhận liên kết đến `xr3myzj7ms51` nhưng không gọi tool đọc incident đó trước khi trả lời. Nguyên nhân có thể là prompt chưa yêu cầu rõ việc đọc tiếp incident liên quan.

## 3. Thay đổi đã thực hiện

- Sửa gì, ở đâu: Cập nhật prompt và loop trong `agent.py`: yêu cầu đọc incident được liên kết khi cần điều tra nguyên nhân/ảnh hưởng; kiểm tra URL nguồn từ tool thành công và yêu cầu sửa nếu thiếu, trong `max_steps`. Toàn bộ 46 tests đạt.
- Vì sao chọn thay đổi này: H6 kết luận trước khi đọc incident liên quan; chỉ dẫn URL chưa chứng minh đã đọc nguồn.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng | 80.45/100 | 77.64/100 |
| Điểm case đã chọn | H6: 60/100 | H6: 75/100 |
| Số model calls | Agent: 49; judge: 22 | Agent: 60; judge: 22 |
| Token, chi phí nếu có | 85,989 tokens; 0.0184554 USD | 123,083 tokens; 0.0243174 USD |

- Lỗi đã giải quyết: H6 đã đọc incident liên quan và dẫn URL nguồn, tăng từ 60 lên 75 điểm. Cả hai lần chấm đủ 22 case, cùng cấu hình; điểm tổng giảm 2.81, số agent calls tăng 11.
- Lỗi còn lại hoặc mới xuất hiện: H2 thiếu `get_status` (100 → 50); H5 nhầm thời điểm cập nhật với thời điểm kết thúc incident (100 → 45); H7 vẫn kết luận operational khi tool timeout.

## 5. Giới hạn

- Điểm judge là ước lượng, có thể sai hoặc thiên lệch.
- Snapshot ngày 09/11/2026 không phản ánh trạng thái live và bị giới hạn dữ liệu trả về.
- Kiểm tra có URL nguồn chưa chứng minh mọi khẳng định đều được nguồn hỗ trợ.
- Một lần chạy mỗi phiên bản chưa chứng minh độ ổn định hoặc xác định toàn bộ chênh lệch điểm là do thay đổi code.
