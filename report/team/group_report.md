# Báo cáo nhóm — Lab 8 LogiX-VN

*Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ các file trong `src/reports/`.*

## 1. Thông tin nhóm

- **Tên nhóm:** DEF
- **Thành viên:** Xem `TEAM.md`.
- **Commit chốt (trùng `report/team/decision_adr.md`):** `6dbe62b`
- **Repository:** https://github.com/Nesto08/K5-L3A-DAY08-DEF-FromWorkflowstoAgents

## 2. Mục tiêu và cách tiếp cận

Nhóm thực hiện Lab Day 08 — *From Workflows to Agents* với mục tiêu xây dựng và so sánh các kiến trúc xử lý yêu cầu hoàn phí vận chuyển tại LogiX-VN.

Bài toán yêu cầu hệ thống xác minh thông tin claim và đơn hàng, kiểm tra quyền truy cập, đối chiếu chính sách hiện hành, tính toán khoản bồi hoàn và thực hiện refund an toàn. Hệ thống phải bảo đảm ba điều kiện quan trọng: không hoàn tiền khi thiếu approval hợp lệ, không làm lộ thông tin nhạy cảm và không tạo refund trùng khi crash/retry.

Nhóm phân chia công việc theo ba kiến trúc:

- **Workflow (Shape A):** Nguyễn Bá Quang phụ trách, triển khai quy trình xử lý bằng Python theo các bước cố định.
- **Single Agent (Shape B):** Bùi Nguyễn Dũng phụ trách, sử dụng vòng lặp ReAct để lựa chọn công cụ và xử lý claim.
- **Orchestrator (Shape C):** Hoàng Văn Bảo phụ trách, xây dựng cơ chế điều phối Investigator và handoff an toàn.
- **Swarm (Shape D):** Sử dụng kiến trúc tham chiếu có sẵn trong lab để đối chiếu kết quả.

Quy trình thực hiện gồm nghiên cứu contract và business rules, triển khai ba Shape trên các branch riêng, bổ sung kiểm thử, tích hợp vào `main`, chạy benchmark cùng bộ dữ liệu và lựa chọn kiến trúc dựa trên chất lượng, chi phí và mức độ an toàn.

## 3. Giải pháp

**Shape A — Workflow**

Workflow xử lý claim theo trình tự cố định: đọc claim, xác minh quyền xem đơn hàng, tính khoản bồi hoàn bằng `compute_compensation`, gọi host qua `issue_refund()` và trả kết quả bằng `RunResult`.

Các trường hợp claim không tồn tại, thiếu mã đơn, không tìm thấy đơn, không có quyền truy cập hoặc quote bằng 0 đều được xử lý theo nhánh nghiệp vụ tương ứng. Workflow giữ nguyên quote đề xuất để host kiểm tra approval, giới hạn tổng tiền hoàn và idempotency.

**Shape B — Single Agent**

Single Agent sử dụng `run_react()` với giới hạn tối đa 8 bước. Agent khai thác các công cụ đọc thông tin như `lookup_order`, `lookup_policy`, `lookup_refund_history` và `compute_compensation`.

MockLLM hỗ trợ lựa chọn công cụ nhưng không được trực tiếp ghi tiền. Kết quả được quản lý thông qua `Budget`, `Trace` và `finish()`. Thao tác refund do host thực hiện, bảo đảm kiểm soát approval và chống hoàn tiền trùng khi crash/retry.

**Shape C — Orchestrator**

Orchestrator điều phối Investigator để thu thập dữ liệu. Investigator chỉ được sử dụng các công cụ đọc. Thông tin handoff được sanitize theo allowlist nhằm loại bỏ dữ liệu không cần thiết hoặc nhạy cảm.

Khoản hoàn được tính bằng code; MockLLM chỉ hỗ trợ tạo bản nháp và không có quyền sửa quote hoặc thực hiện refund. Host chịu trách nhiệm cuối cùng đối với các thao tác tài chính.

**Ranh giới Code / Model và Trace**

Ba Shape tuân thủ nguyên tắc model chỉ hỗ trợ phân tích và lựa chọn công cụ, còn code và host kiểm soát chính sách, số tiền và thao tác ghi ledger.

Trace của Workflow ghi các event `claim_lookup`, `order_lookup`, `quote`, `refund_outcome` và `decision`. Các nhánh trả về sớm vẫn sử dụng `finish()` để tạo trace và kết quả hợp lệ.

Hệ thống không đưa ticket thô, secret, số điện thoại, địa chỉ hoặc dữ liệu cá nhân vào trace và handoff. Nội dung ticket được xem là dữ liệu không đáng tin cậy, không được dùng để ghi đè dữ liệu đơn hàng chính thức.

## 4. Kết quả

**Benchmark bốn Shape trên bộ public**

Nguồn: `src/reports/benchmark.json`.

Benchmark sử dụng 14 claim và năm seed `11, 22, 33, 44, 55`, tương đương 70 trial mỗi Shape và 280 trial tổng cộng. Các điều kiện về dữ liệu, MockLLM, bảng giá và evaluator được giữ cố định; mỗi trial sử dụng SQLite riêng.

| Chỉ số | Workflow | Single | Orchestrator | Swarm |
|---|---:|---:|---:|---:|
| Pass rate | 100% | 100% | 100% | 98,57% |
| Pass^5 | 100% | 100% | 100% | 92,86% |
| Seed min–max | 100–100% | 100–100% | 100–100% | 92,86–100% |
| Variance | 0 | 0 | 0 | 0,000816 |
| Cost/success (VND mô phỏng) | 27,86 | 49,90 | 37,37 | 49,57 |
| Mean steps | 4,43 | 5,36 | 4,71 | 2,80 |
| P95 steps | 5 | 6 | 5 | 3 |

Workflow, Single Agent và Orchestrator đều đạt 70/70 trial thành công. Swarm đạt 69/70, thất bại ở claim `C-002`, seed 55 do sử dụng thông tin ngày giao trễ từ ticket thay vì dữ liệu order.

Workflow có chi phí mô phỏng thấp nhất, trong khi Swarm có số bước trung bình thấp nhất. Tuy nhiên, số bước là số event trace, không phản ánh trực tiếp tốc độ xử lý thực tế.

**Crash Safety và kiểm thử**

Nguồn: `src/reports/crash.json`.

Crash Safety Suite đạt **20/20**, gồm các tình huống crash trước effect, sau effect nhưng trước checkpoint, sau checkpoint và retry bất thường.

Các test T11, T12, T13 và T14 kiểm tra idempotency, crash/resume và giới hạn hoàn tiền. Kết quả kiểm thử toàn bộ nhóm sau khi xử lý conflict là **317 passed**.

Run ID dẫn chứng: `R-workflow-C-001-s11`.

**Quyết định kiến trúc và lý do**

Theo `report/team/decision_adr.md`, nhóm lựa chọn **Shape A — Workflow**.

Workflow đạt chất lượng tương đương Single Agent và Orchestrator trên bộ public nhưng có chi phí thấp nhất (27,86 VND mô phỏng/success). Các bước xử lý nghiệp vụ có thứ tự phụ thuộc rõ ràng, không cần tăng quyền tự chủ khi chưa có lợi ích đo được.

**Phiếu nghiên cứu và ablation**

Theo `report/team/research_card.md` và `src/reports/bonus_r1_ablation.json`, Workflow có và không có Investigator đều đạt 70/70 trial. Tuy nhiên, cost/success tăng từ 27,86 lên 66,24 VND mô phỏng khi bổ sung Investigator, tương đương khoảng 2,38 lần.

Với bonus B1, xử lý song song các thao tác đọc độc lập giúp critical-path latency mô phỏng trung bình giảm từ 258,686 ms xuống 218,943 ms, tương ứng speedup khoảng 1,18 lần. Đây là kết quả mô phỏng, không phải wall-clock latency.

## 5. Khó khăn và cách xử lý

**Thiết lập môi trường:** PowerShell chặn `Activate.ps1` và môi trường Python ban đầu thiếu thư viện. Nhóm sử dụng Python executable trong `.venv`, cài dependencies và xác nhận Smoke Test thành công.

**Triển khai các Shape:** Các file ban đầu còn `not_implemented`, khiến nhiều test thất bại. Nhóm hoàn thiện logic nghiệp vụ, kết nối read tools, chuẩn hóa `RunResult` và kiểm tra trace.

**Crash Safety:** Việc chương trình bị gián đoạn sau khi ghi tiền nhưng trước checkpoint có nguy cơ gây refund trùng. Nhóm truyền `crash_at` xuống host và kiểm thử cơ chế idempotency qua T11, T12 cùng Crash Safety Suite. Kết quả đạt 20/20.

**Tích hợp code:** Các thành viên phát triển trên branch riêng và tích hợp vào `main`. Trong quá trình tích hợp, nhóm xử lý conflict liên quan đến bonus import, sau đó chạy lại kiểm thử bằng lệnh:

`python -m pytest -q -o addopts= --basetemp=.adr-verified-tests -p no:cacheprovider`

Kết quả ghi nhận: **317 passed**.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp được ghi trong `TEAM.md`, lịch sử commit và báo cáo cá nhân thuộc `report/team/`.

| Thành viên | Phần việc và bằng chứng |
|---|---|
| **Nguyễn Bá Quang — 2A202603555** | Shape A — Workflow; xử lý claim, trace và test. Tham gia research card R1 và ablation. File `workflow.py`, `test_workflow.py`. Commit `2b8a01d`, `2e68912`, `3ad4d06`. |
| **Bùi Nguyễn Dũng — 2A202603587** | Shape B — Single Agent; tích hợp ReAct, Budget, Trace, host-only refund và crash safety. File `single.py`; bộ lọc Single Agent đạt 122 passed, T12 passed, Crash Safety 20/20. Branch `dung`. |
| **Hoàng Văn Bảo — 2A202603549** | Shape C — Orchestrator, Investigator và bonus B1; xây dựng handoff an toàn, xử lý song song và kiểm thử. Commit `218709d`; bonus B1 có 10 test passed. |

## 7. Hạn chế và hướng cải thiện

Hệ thống sử dụng MockLLM nên kết quả chưa phản ánh đầy đủ hành vi của model sản xuất. Cost/success được tính theo bảng giá mô phỏng của lab, không phải chi phí API thực tế. Latency trong benchmark chính là `unavailable`.

Bộ public chỉ gồm 14 claim và năm seed; kết quả 100% public không bảo đảm hệ thống đạt cùng chất lượng trên hidden claims. Nhóm chưa có kết quả hidden chính thức để đánh giá khả năng tổng quát hóa.

Crash suite 20/20 chủ yếu kiểm tra host và Swarm, không thay thế test crash/resume riêng của Workflow.

Hướng cải thiện là mở rộng dữ liệu thử nghiệm, kiểm tra các tình huống policy thay đổi, prompt injection, approval không hợp lệ và lỗi gián đoạn phức tạp hơn. Khi triển khai thực tế, cần đo latency, chi phí API và chất lượng trên các nguồn dữ liệu đa dạng.

Nhóm sẽ xem xét chuyển sang Single Agent hoặc Orchestrator nếu các thử nghiệm cùng điều kiện cho thấy lợi ích rõ ràng về độ chính xác hoặc hiệu quả, đủ bù đắp chi phí và độ phức tạp tăng thêm, đồng thời vẫn đáp ứng đầy đủ các điều kiện an toàn.
