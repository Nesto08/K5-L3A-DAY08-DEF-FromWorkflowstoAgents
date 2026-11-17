# Team

## Thông tin nhóm

- Tên nhóm: DEF
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-DEF-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: `https://github.com/Nesto08/K5-L3A-DAY08-DEF-FromWorkflowstoAgents`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Bùi Nguyên Dũng | 2A202603587 | dung208042@gmail.com | https://github.com/Nesto08 | Single |
|   2 | Hoàng Văn Bảo   | 2A202603549 | 26ai.baohv@vinuni.edu.vn | https://github.com/BaoAIuet | Orchestrator + Investigator + B1 |
|   3 | Nguyễn Bá Quảng | 2A202603555 | nbquang04@gmail.com | https://github.com/nbquang04 | Workflow |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Bá Quảng | Phụ trách Shape A — Workflow: triển khai luồng xử lý claim, kiểm tra quyền, tính quote, gọi host hoàn tiền và ghi trace; đóng góp một phần vào research card R1 — Scaling (`report/team/research_card.md`) và thí nghiệm ablation workflow có/không có investigator. | `2b8a01d` (workflow và test); `2e68912` (báo cáo cá nhân); `3ad4d06` (đóng góp research card và ablation) | `src/tests/test_workflow.py::test_unknown_claim_has_trace_without_changing_ledger`; `src/tests/test_bonus_r1.py` (T02 seed 55, T13, T14, crash/resume T12). |
| Hoàng Văn Bảo | Orchestrator + Investigator, bonus B1 | `bao@218709d` | `src/tests/test_bonus_b1_parallel.py` — 10 passed |
| Tên | Shape B — Single Agent (ReAct), CP2/CP3, Budget, Trace, host-only refund và crash safety | 2ae2846 (Single và báo cáo cá nhân) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603587_BuiNguyenDung

- Phần việc phụ trách

    - Phụ trách Shape B — Single Agent (ReAct) trong Lab Day 08.
    - Triển khai CP2 (ReAct Agent) và CP3 (Crash Safety).
    - Kiểm thử chức năng và độ an toàn của Single Agent.

- Đóng góp cụ thể

    - Hoàn thiện src/lab8/shapes/single.py, thay thế phần not_implemented bằng logic xử lý claim.
    - Tích hợp run_react() với giới hạn tối đa 8 bước, sử dụng MockLLM và các công cụ đọc dữ liệu.
    - Đảm bảo Agent không trực tiếp ghi tiền; chỉ host được phép thực hiện refund.
    - Tích hợp Budget, Trace và cơ chế chống hoàn tiền trùng khi crash/retry.
    - Kiểm tra kết quả bằng pytest và Crash Safety Suite.

- Bằng chứng

    - Branch: dung
    - File: src/lab8/shapes/single.py
    - Pytest: 122 passed, 180 deselected (bộ lọc Single Agent).
    - Test test_t12_crash_before_checkpoint_does_not_double_pay[single]: PASSED.
    - Crash Safety Suite: 20/20.
    - Commit: 2ae2846 (Single, báo cáo cá nhân)

## 2A202603555_NguyenBaQuang


### Phần việc phụ trách

- Phụ trách Shape A — Workflow trong `src/lab8/shapes/workflow.py`.
- Bổ sung kiểm thử cho workflow và viết báo cáo cá nhân.
- Đóng góp một phần vào research card R1 — Scaling và thí nghiệm so sánh workflow có/không có investigator chỉ đọc.

### Đóng góp cụ thể

- Triển khai luồng xử lý claim theo thứ tự cố định: đọc claim, kiểm tra quyền xem order, tính quote bằng `compute_compensation`, gọi host qua `issue_refund` và trả kết quả có trace.
- Xử lý các trường hợp claim không tồn tại, thiếu mã đơn, không tìm thấy đơn hoặc không có quyền xem, quote bằng 0 và kết quả chấp nhận/từ chối/conflict từ host.
- Giữ nguyên quote đề xuất, để host kiểm tra approval, trần hoàn tiền theo đơn và idempotency; truyền `crash_at` xuống host để hỗ trợ kiểm thử crash/resume.
- Ghi trace ở các nhánh trả kết quả, không ghi nội dung ticket thô, secret hoặc thông tin cá nhân; đóng kết nối cơ sở dữ liệu trong `finally`.
- Thêm test cho claim không tồn tại, kiểm tra trạng thái trả về, trace hợp lệ và việc không thay đổi ledger hoặc tạo audit.
- Đóng góp một phần vào nội dung research card R1, biến thể investigator chỉ đọc, kết quả benchmark ablation và các test hồi quy liên quan. Kết quả public ghi nhận pass rate không đổi, trong khi cost/success mô phỏng tăng khoảng 2,38 lần; kết luận giới hạn trong thiết lập MockLLM và bộ claim public của lab.

### Bằng chứng

- Code: `src/lab8/shapes/workflow.py`; biến thể ablation: `src/bonus/r1_investigator.py`.
- Test: `src/tests/test_workflow.py::test_unknown_claim_has_trace_without_changing_ledger`; `src/tests/test_bonus_r1.py` kiểm tra T02 seed 55, T13, T14 và crash/resume T12.
- Kết quả đã ghi nhận trong báo cáo cá nhân: 62 passed, 241 deselected cho ma trận student riêng workflow; 55 passed, 248 deselected cho bộ test mặc định tại thời điểm kiểm tra.
- Kết quả ablation: mỗi cấu hình đạt 70/70 trial public; cost/success mô phỏng tăng từ 27,86 lên 66,24 VND khi thêm investigator. Dữ liệu lưu tại `src/reports/bonus_r1_ablation.json`.
- Báo cáo: `report/team/2A202603555_NguyenBaQuang.md`; đóng góp chung: `report/team/research_card.md`.
- Commit: `2b8a01d` (workflow và test), `2e68912` (báo cáo cá nhân), `3ad4d06` (đóng góp research card và ablation).

## 2A202603549_HoangVanBao

### Phần việc phụ trách

- Phụ trách Shape C — Orchestrator + Investigator và bonus B1.
- Giữ investigator ở quyền đọc-only; chỉ host được phép ghi refund vào ledger.

### Đóng góp cụ thể

- Triển khai orchestrator với handoff theo allowlist, quote bằng code và một lời gọi MockLLM để draft; output model không ảnh hưởng quote hoặc refund.
- Thêm B1 chạy song song các lượt đọc độc lập `lookup_order` và `lookup_policy`; quote và refund vẫn tuần tự, mỗi worker dùng SQLite connection riêng.
- Thêm seeded latency, critical-path estimator và test parity, thứ tự hoàn thành, latency, crash/resume.

### Bằng chứng

- Branch: `bao`
- Files: `src/lab8/shapes/orchestrator.py`, `src/bonus/orchestrator_parallel.py`, `src/bonus/latency.py`, `src/bonus/critical_path.py`
- Commit: `218709d`
- Test `python -m pytest src/tests/test_bonus_b1_parallel.py`: 10 passed.
- Public benchmark B1: 70/70 trial cho cả serial và parallel; critical-path latency là ước tính deterministic, không phải wall-clock.
