# Báo cáo cá nhân — 2A202603555_NguyenBaQuang

## 1. Thông tin thành viên

- Họ tên: Nguyễn Bá Quảng
- MSSV: 2A202603555
- Email: nbquang04@gmail.com
- GitHub: https://github.com/nbquang04

## 2. Phần việc phụ trách

Phụ trách Shape A — workflow trong `src/lab8/shapes/workflow.py` và test bổ sung trong `src/tests/test_workflow.py`. Phạm vi gồm đọc claim, kiểm tra quyền xem order, tính số tiền đề xuất, gọi host hoàn tiền và trả kết quả có trace.

## 3. Đóng góp cụ thể

- Hoàn thiện workflow theo thứ tự Python cố định, giữ nguyên chữ ký `run_claim`. Workflow không gọi model; số tiền được tính bằng `compute_compensation` từ order có cấu trúc, không lấy số ngày trễ hoặc mã đơn từ nội dung ticket.
- Xử lý các nhánh claim không tồn tại (`failed`), thiếu mã đơn (`needs_info`), không tìm thấy đơn hoặc không có quyền xem (`escalated`), quote bằng 0 (`denied`) và kết quả chấp nhận/từ chối/conflict từ host.
- Truyền quote đầy đủ vào `issue_refund`; host kiểm approval, trần hoàn tiền theo đơn và idempotency. Không tự trừ số tiền đã hoàn trước đó. `proposal_amount` giữ nguyên quote ngay cả khi host chỉ hoàn phần chênh lệch.
- Truyền `crash_at` xuống host, để `InjectedCrash` lan ra và đóng connection trong `finally`, phục vụ kiểm tra crash/resume.
- Dùng `finish()` để lấy effect và số audit từ ledger, đồng thời ghi trace ở mọi nhánh trả kết quả. Trace chỉ ghi trạng thái lookup, quote và kết quả host; không dump ticket, claim/order thô, secret, header hoặc PII.
- Thêm test `test_unknown_claim_has_trace_without_changing_ledger`: kiểm tra claim không tồn tại trả kết quả đúng, có trace hợp lệ, không làm thay đổi ledger và không tạo audit cho claim đó.
- Commit chính: `2b8a01d` — Implement deterministic workflow and unknown-claim test.

## 4. Bằng chứng

| Bằng chứng | Kết quả |
| --- | --- |
| Code | `src/lab8/shapes/workflow.py` |
| Test bổ sung | `src/tests/test_workflow.py::test_unknown_claim_has_trace_without_changing_ledger` |
| Ma trận student riêng workflow | 62 passed, 241 deselected |
| Bộ test mặc định gồm host và test bổ sung tại thời điểm chạy | 55 passed, 248 deselected |

Các lệnh tái lập kết quả, chạy trong thư mục `src/`:

```powershell
python -m pytest -q -m student -o addopts= -k workflow
python -m pytest -q
```

Ma trận student kiểm tra các tình huống nghiệp vụ T01–T14, bao gồm retry không tạo refund trùng (T11), crash rồi resume (T12), đơn đã được hoàn đủ (T13) và chỉ hoàn phần chênh lệch (T14). Test bổ sung kiểm tra nhánh claim không tồn tại, tính hợp lệ của trace và việc giữ nguyên ledger. Các kết quả trên thuộc bộ test public, chưa phải kết quả hidden hoặc benchmark đủ bốn shape.

## 5. Công cụ AI đã dùng

- Công cụ: Codex.
- Mục đích sử dụng: hỗ trợ đọc yêu cầu, giải thích luồng workflow và các khái niệm approval, giới hạn tổng tiền hoàn theo đơn, idempotency; hỗ trợ viết code và test bổ sung.
- Phạm vi hỗ trợ: triển khai các nhánh xử lý trong `workflow.py`, sử dụng các hàm host có sẵn, ghi trace và bổ sung test cho claim không tồn tại.
- Cách kiểm chứng kết quả AI: sử dụng ma trận student của đề và test bổ sung để đối chiếu trạng thái, số tiền đề xuất, ledger, audit và trace. Việc chạy test được Codex hỗ trợ thực hiện; kết quả và lệnh tái lập được ghi ở mục 4.

## 6. Tự đánh giá

Về sản phẩm kỹ thuật, workflow đã qua 62 test public dành riêng cho shape; bộ test host và test bổ sung cũng xanh trong lần kiểm tra đã ghi nhận. Chưa có kết quả hidden hoặc benchmark toàn nhóm để kết luận về hiệu quả so với các kiến trúc khác. Workflow hiện không gọi model, nên giới hạn của đánh giá là task và fixture của lab; kết quả không chứng minh hiệu năng trên dữ liệu sản xuất.

Về tự đánh giá cá nhân, chưa ghi nhận mức độ tự giải thích hoặc tự chạy lại của thành viên trong phiên này. Thành viên cần xác nhận và bổ sung nhận xét của mình sau khi trực tiếp rà soát code. Các việc còn lại trước khi nộp là bổ sung commit hash, cập nhật bảng đóng góp trong `TEAM.md` và phối hợp với nhóm để tích hợp benchmark/báo cáo chung.
