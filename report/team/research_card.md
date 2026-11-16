# Research card

Nhóm chọn R1 — Scaling để đánh giá ảnh hưởng của việc thêm một investigator chỉ đọc vào workflow xử lý claim. Nhóm thực hiện ablation bằng cách bật/tắt bước investigator, giữ nguyên luồng quyết định và ghi refund.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Nhóm trình bày nguồn tham khảo, giả thuyết và phương pháp thực nghiệm trong bảng dưới đây.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 — Scaling: thêm investigator vào luồng claims chủ yếu tuần tự có mang lại lợi ích không? |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research, 28/01/2026, [Towards a science of scaling agent systems: When and why agent systems work](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/). Blog nghiên cứu tóm tắt benchmark 180 cấu hình; paper gốc: https://arxiv.org/abs/2512.08296 (bản đầu năm 2025). |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trong thiết lập của nghiên cứu, lợi ích của multi-agent phụ thuộc khả năng phân rã task; phối hợp nhiều agent có thể làm giảm hiệu quả trên task cần suy luận tuần tự. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Nguồn đánh giá 5 kiến trúc trên Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench, với các họ model GPT, Gemini, Claude. Không phải benchmark LogiX hay MockLLM; không chuyển trực tiếp mức tăng/giảm của nguồn sang lab. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nhóm dự đoán khi thêm một investigator chỉ đọc để kiểm tra lại quote trước workflow, pass rate và pass^5 không đổi (chênh 0 điểm phần trăm), còn cost/success mô phỏng tăng ít nhất 2 lần do đọc lại dữ liệu và thêm một lần gọi MockLLM ở các claim có order_id. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Bật/tắt bước investigator bổ sung. Baseline là workflow hiện có; biến thể trong bonus/r1_investigator.py gọi investigator rồi dùng nguyên hàm workflow cho quyết định và ghi tiền. Cố định tool implementation, MockLLM backend, 14 claim public, world state, seed 11/22/33/44/55, pricing, as_of và evaluator. Mỗi trial có SQLite mới. Số lần gọi model/tool tăng là hệ quả của bước bổ sung. Không sửa host, dữ liệu hay thước đo. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Rủi ro investigator tin ticket sai, lộ context hoặc ảnh hưởng trần theo đơn; dùng handoff allowlist, chỉ tool đọc và dữ liệu order có cấu trúc. Đo pass rate, pass^5, seed min–max, variance, cost/success và steps bằng evaluator có sẵn. Test thêm T02 seed 55, T13, T14 và crash/resume T12. Không suy ra safety counts hidden từ pass rate public. |

## Kết quả ablation

Nhóm sử dụng lệnh benchmark sau trong thư mục `src/` để so sánh hai cấu hình:

```powershell
python -m lab8.benchmark --shapes workflow,workflow_investigator --extra-shape workflow_investigator=bonus.r1_investigator:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/bonus_r1_ablation.json
```

- Nhóm lưu kết quả do benchmark sinh tại `src/reports/bonus_r1_ablation.json`. Mỗi cấu hình có 70 trial (14 claim × 5 seed), tổng cộng 140 trial.
- Run id dẫn chứng: `R-workflow-C-001-s11` và `R-workflow_investigator-C-001-s11`; danh sách đầy đủ nằm trong trường `trials` của JSON.
- Nhóm triển khai biến thể tại `src/bonus/r1_investigator.py` và sử dụng nguyên hàm baseline tại `src/lab8/shapes/workflow.py` cho phần quyết định và ghi refund.

| Metric | Workflow | Workflow + investigator |
| --- | ---: | ---: |
| Trial pass | 70/70 | 70/70 |
| Pass rate | 1,000 | 1,000 |
| Pass^5 | 1,000 | 1,000 |
| Seed min–max | 1,000–1,000 | 1,000–1,000 |
| Seed variance | 0 | 0 |
| Cost/success mô phỏng (VND) | 27,86 | 66,24 |
| Mean / p95 steps | 4,43 / 5 | 6,29 / 7 |
| Mean model calls | 0 | 0,93 |
| Mean tool calls | 2,79 | 6,50 |

Số model call trung bình nhỏ hơn 1 vì claim thiếu order_id không chạy investigator. Bước đọc claim để kiểm tra điều kiện vẫn được tính chi phí ở biến thể.

- Nhóm ghi nhận kết quả phù hợp với hypothesis trong phạm vi thí nghiệm: pass rate không đổi, còn cost/success tăng khoảng 2,38 lần (+137,8%). Investigator kiểm tra lại cùng nguồn dữ kiện không sửa thêm lỗi nào trên bộ public.
- Quan hệ phụ thuộc: cần claim để biết order/principal; cần order để tính quote; cần quote trước khi host kiểm duyệt và ghi refund. Policy có thể được đọc độc lập với order, nhưng thí nghiệm này không triển khai chạy song song hoặc đo critical path.
- Từ kết quả trên, nhóm giữ workflow không có investigator bổ sung cho phạm vi thử nghiệm hiện tại. Nhóm sẽ xem xét lại lựa chọn nếu task xuất hiện dữ kiện độc lập mà workflow bỏ sót hoặc investigator có thể phát hiện lỗi mới với chi phí chấp nhận được.

Nhóm sử dụng bộ test hồi quy để kiểm tra việc bổ sung investigator không làm sai nghiệp vụ hoặc cơ chế crash/resume. Lệnh kiểm tra trong `src/`:

```powershell
python -m pytest -q --basetemp=.r1-test-verify -p no:cacheprovider
```

Kết quả kiểm tra: **59 passed, 248 deselected**, gồm 4 test mới trong `src/tests/test_bonus_r1.py` cho T02 seed 55, T13, T14 và crash/resume T12.

Nhóm xác định các giới hạn của thí nghiệm như sau:

- MockLLM không phải model sản xuất; latency là `unavailable`, không kết luận về tốc độ hoặc lợi ích song song.
- Investigator kiểm tra lại dữ kiện bằng tool có sẵn và một phản hồi MockLLM, không thực hiện suy luận độc lập. Investigator không được quyền đổi quote cuối hay ghi tiền, nên việc giữ nguyên quyết định là hệ quả thiết kế. Nhóm chỉ đánh giá chi phí bổ sung của bước này, không khái quát kết luận cho mọi loại investigator.
- Baseline đã đạt 100% public nên không còn dư địa tăng pass rate trên corpus này. Chưa đánh giá hidden, chưa chứng minh ý nghĩa thống kê hoặc tái lập mức giảm hiệu năng trong nghiên cứu gốc.
- Nhóm thực hiện thí nghiệm này cho research card R1; phạm vi không bao gồm triển khai investigator song song theo topic bonus B1.
