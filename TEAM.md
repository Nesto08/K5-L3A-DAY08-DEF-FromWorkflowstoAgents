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
|   2 | Hoàng Văn Bảo   | 2A202603549 | 26ai.baohv@vinuni.edu.vn | https://github.com/BaoAIuet | Orchestrator + Swarm |
|   3 | Nguyễn Bá Quảng | 2A202603555 | nbquang04@gmail.com | https://github.com/nbquang04 | Workflow |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| | | | |

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
    - Commit:

## MSSV_HoTen


### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## MSSV_HoTen


### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
