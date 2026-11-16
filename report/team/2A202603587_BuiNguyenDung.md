# Báo cáo cá nhân — MSSV_HoTen

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Bùi Nguyên Dũng
- MSSV: 2A202603587
- Email: dung208042@gmail.com
- GitHub: https://github.com/Nesto08

## 2. Phần việc phụ trách

Phụ trách triển khai **Shape B — Single Agent (ReAct)** trong Lab Day 08 — From Workflows to Agents.

- Module chính: `src/lab8/shapes/single.py`.
- Hoàn thiện CP2: xây dựng Single Agent sử dụng `lab8.runtime.run_react` với giới hạn tối đa 8 bước.
- Hoàn thiện CP3: tích hợp cơ chế hoàn tiền an toàn, xử lý crash và tránh hoàn tiền trùng.
- Kiểm thử chức năng, độ ổn định và tính an toàn của Single Agent.

## 3. Đóng góp cụ thể

**Commit chính:** 

**Các thay đổi đã thực hiện:**

- Thay thế phần `not_implemented` bằng logic xử lý claim trong `run_claim()`, giữ nguyên cấu trúc và chữ ký hàm ban đầu.
- Tích hợp vòng lặp ReAct để Agent sử dụng các công cụ đọc dữ liệu đơn hàng, chính sách và lịch sử hoàn tiền.
- Sử dụng dữ liệu đơn hàng làm nguồn thông tin đáng tin cậy, không để nội dung ticket ghi đè dữ liệu thực tế.
- Giới hạn số bước ReAct ở mức 8, sử dụng `Budget` để thống kê model calls, tool calls và chi phí.
- Tách quyền ra quyết định của Agent khỏi quyền ghi tiền; chỉ host được phép gọi `durability.issue_refund()`.
- Truyền `crash_at` vào `issue_refund()` và đảm bảo `InjectedCrash` được truyền ra ngoài để kiểm tra cơ chế phục hồi.
- Sử dụng `finish()` và `Trace` để trả về kết quả theo đúng contract và ghi trace JSON.

**Quyết định kỹ thuật:**

Ưu tiên sử dụng dữ liệu đáng tin cậy từ database và cơ chế kiểm soát của host thay vì cho Agent tự quyết định số tiền hoàn hoặc trực tiếp ghi dữ liệu tài chính.

Chưa có bằng chứng trong cuộc trao đổi về việc thêm hoặc chỉnh sửa file test riêng; phần kiểm thử được thực hiện bằng bộ test có sẵn của lab.

## 4. Bằng chứng

**Repository:** https://github.com/Nesto08/K5-L3A-DAY08-DEF-FromWorkflowstoAgents

**Branch:** `dung`

**Commit:** 

**Kết quả kiểm thử:**

- Smoke Test: `lab8.smoke pass`.
- Môi trường: Python 3.12.10, Windows AMD64, MockLLM seeded.
- Pytest với bộ lọc Single Agent: **122 passed, 180 deselected**, thời gian 5.93 giây.
- Test `test_t12_crash_before_checkpoint_does_not_double_pay[single]`: **PASSED**.
- Crash Safety Suite: **20/20**.

Các lệnh kiểm thử đã thực hiện:

```powershell
python -m lab8.smoke

python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator" --tb=short

python -m pytest -v -o addopts= -k "test_t12_crash_before_checkpoint_does_not_double_pay and single"

python -m lab8.crash_test --count 20 --out reports/crash.json
```

Các kết quả trên là bằng chứng kiểm thử công khai. Chưa xác nhận kết quả hidden tests và benchmark cuối cùng của nhóm.

## 5. Công cụ AI đã dùng

**Công cụ:** ChatGPT (OpenAI).

**Mục đích sử dụng:**

- Giải thích yêu cầu CP2, CP3 và cơ chế hoạt động của Single Agent theo kiến trúc ReAct.
- Hỗ trợ phân tích `runtime.py`, `schemas.py`, `common.py`, `trace.py` và các contract liên quan.
- Hỗ trợ xây dựng và chỉnh sửa logic trong `single.py`, giữ nguyên cấu trúc code khung của giảng viên.
- Phân tích lỗi pytest, xác định nguyên nhân test thất bại và đề xuất hướng kiểm tra.

## 6. Tự đánh giá

Đã hoàn thiện phần triển khai Single Agent theo phạm vi được phân công và vượt qua các kiểm thử công khai đã chạy.

Qua bài lab, hiểu rõ hơn sự khác biệt giữa Workflow và Agent, cách triển khai vòng lặp ReAct, quản lý giới hạn bước và thống kê chi phí. Đặc biệt, nhận thức được tầm quan trọng của việc tách quyền sử dụng công cụ của Agent khỏi các thao tác có tác động tài chính.

Điểm đạt được là Single Agent đã vượt qua bộ test được chọn và bài kiểm tra crash safety. Tuy nhiên, vẫn cần phối hợp với các thành viên khác để chạy benchmark tổng thể, đánh giá hiệu quả giữa các kiến trúc và kiểm tra khả năng đáp ứng hidden tests.

Bài học quan trọng nhất là **Agent có thể tự chủ trong việc thu thập thông tin, nhưng các thao tác có rủi ro cao phải được kiểm soát bằng logic và cơ chế thực thi đáng tin cậy của hệ thống.**