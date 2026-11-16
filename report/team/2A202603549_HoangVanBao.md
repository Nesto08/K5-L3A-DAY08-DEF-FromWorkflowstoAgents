# Báo cáo cá nhân — 2A202603549_HoangVanBao

## 1. Thông tin thành viên

- Họ tên: Hoàng Văn Bảo
- MSSV: 2A202603549
- Email: 26ai.baohv@vinuni.edu.vn
- GitHub: BaoAIuet

## 2. Phần việc phụ trách

Tôi phụ trách phần orchestrator + investigator trong bài lab này. Cụ thể:

- Triển khai `src/lab8/shapes/orchestrator.py`.
- Thiết kế handoff theo allowlist để tránh lộ secret và dữ liệu nhạy cảm.
- Chỉ cho investigator dùng tool đọc (`lookup_order`, `lookup_policy`, `compute_compensation`, `lookup_refund_history` nếu cần).
- Đảm bảo orchestrator là nơi gọi `issue_refund` ở host; MockLLM chỉ được gọi cho draft và không tham gia quyết định hay ghi ledger.
- Ghi trace theo contract v1, đồng thời không lưu raw secret / header / PII vào trace.

## 3. Đóng góp cụ thể

- Tạo handoff với `make_handoff`, giới hạn fields và tool cho investigator.
- Ràng buộc `facts` trong allowlist; không cho `parent_secret`, `raw_headers`, `phone`, `address`, `internal_note`, `item_name` đi qua handoff.
- Chạy `run_readonly_investigators` để thu thập kết quả đọc-only, sau đó orchestrator tính quote và đưa cho host.
- Dùng quote đầy đủ để gọi `issue_refund`, không trừ phần đã hoàn trước đó ở shape; để host xử lý cap theo đơn và idempotency.
- Tự kiểm trace và crash flow: `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`, retry conflict, no-approval case.
- Theo quyết định chọn B1, phối hợp triển khai biến thể investigator song song: hai read độc lập `lookup_order` và `lookup_policy` chạy trên SQLite connection riêng; quote và refund vẫn tuần tự. Orchestrator tuần tự và B1 mỗi shape gọi MockLLM một lần cho draft, nhưng output không tác động kết quả nghiệp vụ.

## 4. Bằng chứng

Các số liệu benchmark dưới đây được chép từ file JSON do lệnh benchmark sinh ra, không phải số tự ước lượng. Phạm vi là public corpus: 14 claim × 5 seed = 70 trial cho mỗi shape; đây không phải kết quả hidden evaluation.

- File benchmark: `src/reports/benchmark.json`
- File crash: `src/reports/crash.json`

Số liệu thật:

- `workflow` trên `main` hiện tại: pass rate = 1.000; pass^5 = 1.000; variance = 0.000000; cost/success = 28.79 VND; mean steps = 3.79; mean model calls = 1. Nhánh Quang chưa merge; workflow ở nhánh đó không gọi MockLLM.
- `single`: pass rate = 1.000; pass^5 = 1.000; variance = 0.000000; cost/success = 28.80 VND; mean steps = 1.64; mean model calls = 1
- `orchestrator`: pass rate = 1.000; pass^5 = 1.000; variance = 0.000000; cost/success = 37.37 VND; mean steps = 4.71; mean model calls = 1
- `swarm`: pass rate = 0.986; pass^5 = 0.929; variance = 0.000816; cost/success = 49.57 VND; mean steps = 2.80; mean model calls = 3
- `crash_safety`: `20/20` trong crash suite chung (`src/reports/crash.json`). Suite này kiểm tra durability/host và có một kịch bản crash của swarm; không nên hiểu là 20 kịch bản riêng cho orchestrator. Với từng shape, public student matrix cũng kiểm tra resume sau `after_effect_before_checkpoint`.
- B1, cùng public 14 claim × 5 seed (70 trial/shape): serial và parallel đều pass rate `1.000`, pass^5 `1.000`, variance `0.000000`, cost/success `37.37` VND; mean model calls = 1.
- Critical path mô phỏng B1: serial mean/p95 `258.686/287 ms`; parallel `218.943/245 ms`; mean path ratio `1.1815x`. Đây là ước tính deterministic từ `src/bonus/latency.yaml`, không phải wall-clock.

Lệnh đã chạy và kết quả thật:

- `python -m pytest -q -m student -o addopts=` → `248 passed, 54 deselected`
- `python -m pytest -q` → `54 passed, 248 deselected`
- `python -m lab8.smoke` → `lab8.smoke pass`
- `python -m lab8.check_submission` → lần chạy được ghi nhận: `0 FAIL, 1 WARN`; warning báo còn thay đổi chưa commit / commit hash trong tài liệu chưa khớp. Vì vậy không ghi kết quả này là kiểm tra sạch hoàn toàn.
- `python -m pytest -q tests/test_bonus_b1_parallel.py` → `10 passed`.

## 5. Công cụ AI đã dùng

- Công cụ hỗ trợ: Copilot SDK trong VS Code / AI assistant trong môi trường phát triển.
- Mục đích: hiểu yêu cầu lab, đọc code host/shape, đề xuất cách thiết kế orchestrator, và kiểm tra trace / lint / pytest.
- Cách tự kiểm tra: tôi không tin tưởng output AI một cách mù quáng. Mọi đề xuất đều được kiểm bằng các lệnh pytest và benchmark thực tế của repo, và chỉ ghi các số liệu xuất hiện từ file JSON thực thi.

## 6. Tự đánh giá

- Phần orchestrator/investigator của tôi đạt được mục tiêu kỹ thuật chính: an toàn về quyền truy cập, bảo mật trace, và độ chính xác trên benchmark public là 1.000. MockLLM được gọi để draft, nhưng quote/refund không phụ thuộc model.
- Về mặt chi phí, orchestrator cao hơn workflow/single nhưng vẫn trong vùng chấp nhận được trong lab, và không phải là lý do để đánh đồng với swarm vì swarm có variance và pass rate thấp hơn ở seed 55 do tin ticket hơn order row.
- Tôi tự đánh giá là đạt trên bộ public và các test đã chạy. Kết quả này không chứng minh hidden set hoặc production behavior; cần giữ rõ giới hạn đó khi diễn giải. Không dùng số liệu bịa để “làm đẹp” báo cáo.
