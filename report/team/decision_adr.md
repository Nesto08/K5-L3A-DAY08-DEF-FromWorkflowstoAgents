# Decision record

Nhóm DEF chọn kiến trúc dựa trên benchmark cùng 14 claim public và 5 seed, kết hợp kiểm tra nghiệp vụ, retry và crash/resume.

- Shape chọn: workflow
- Commit hash: 6dbe62b
- Run id dẫn chứng: R-workflow-C-001-s11; các trial còn lại nằm trong src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (70/70 trial public)
- Cost per success (mô phỏng, VND): 27.857142857142858 (xấp xỉ 27,86; src/reports/benchmark.json)
- Crash safety: 20/20 (src/reports/crash.json; suite kiểm host và swarm; crash/resume của workflow được kiểm riêng bằng T12 trong ma trận student)
- Secret leak / approval bypass: không ghi nhận vi phạm trong các trial workflow public đã pass và các test liên quan; chưa có safety counts hoặc kết quả hidden chính thức

## Vì sao shape này

Nhóm chọn workflow vì đạt cùng độ đúng với single và orchestrator trên bộ public, có cost/success thấp nhất và mức tự chủ phù hợp với quy trình. Các bước đọc claim, kiểm tra quyền xem order, tính quote và gọi host có thứ tự phụ thuộc rõ ràng; model không cần quyết định số tiền hoặc chọn đường ghi refund. Tiền do `compute_compensation` tính từ dữ liệu order có cấu trúc. Host giữ quyền kiểm approval, giới hạn tổng tiền hoàn theo đơn và idempotency.

Nhóm chạy lại benchmark trên commit code nêu trên, với 14 claim × 5 seed cho mỗi shape, tổng cộng 280 trial. Các điều kiện được giữ cố định gồm world state, `as_of=2026-11-15`, MockLLM, tool, bảng giá và evaluator; mỗi trial có SQLite mới.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success mô phỏng (VND) | Mean / p95 steps |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| Workflow | 1,000000 | 1,000000 | 1,000000–1,000000 | 0 | 27,86 | 4,43 / 5 |
| Single | 1,000000 | 1,000000 | 1,000000–1,000000 | 0 | 49,90 | 5,36 / 6 |
| Orchestrator | 1,000000 | 1,000000 | 1,000000–1,000000 | 0 | 37,37 | 4,71 / 5 |
| Swarm | 0,985714 | 0,928571 | 0,928571–1,000000 | 0,000816327 | 49,57 | 2,80 / 3 |

Số liệu lấy từ `src/reports/benchmark.json`. Swarm fail một trial tại `C-002`, seed 55: dùng số ngày trễ trong ticket thay cho order nên hoàn tiền khi đáng ra phải từ chối. Workflow không có bước ghi đè dữ kiện này. Metric steps đếm event trace, vì vậy số steps ít hơn không chứng minh một shape nhanh hơn hoặc đơn giản hơn.

Các lệnh tái lập, chạy trong `src/`:

```powershell
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
```

## Có đáng đổi lấy multi-agent không

Trong thiết lập hiện tại, nhóm chưa ghi nhận lợi ích về độ đúng khi chuyển từ workflow sang single hoặc orchestrator, trong khi cost/success cao hơn. Swarm vừa có chi phí cao hơn vừa có dao động giữa seed. Do đó, nhóm ưu tiên workflow thay vì tăng mức tự chủ khi chưa có lợi ích đo được.

Thí nghiệm R1 trong `report/team/research_card.md` bổ sung bằng chứng về chi phí kiểm tra lặp: workflow có/không có investigator chỉ đọc đều pass 70/70 trial, nhưng cost/success tăng từ 27,86 lên 66,24 VND mô phỏng, khoảng 2,38 lần. Investigator không được đổi quyết định cuối, nên kết quả này chỉ phản ánh chi phí bước kiểm tra bổ sung, không chứng minh mọi mô hình multi-agent đều kém hiệu quả.

Nhóm sẽ xem xét đổi kiến trúc khi xuất hiện yêu cầu xử lý dữ kiện phi cấu trúc hoặc nhiều nguồn độc lập mà workflow không đáp ứng tốt, và thí nghiệm cùng điều kiện cho thấy kiến trúc mới cải thiện độ đúng hoặc hiệu quả đủ để bù chi phí. Kiến trúc thay thế vẫn phải qua các điều kiện approval, secret/PII và crash safety. Nếu workflow không đạt ngưỡng hidden 0,75, nhóm cần điều tra lỗi và đánh giá lại quyết định.

## Trace và bằng chứng

Trace của workflow ghi các event `claim_lookup` (found), `order_lookup` (visible và reason), `quote` (amount, reason, clause_ids, parts), `refund_outcome` (ok, reason, conflict) và `decision` (status, reason). Các nhánh trả về sớm cũng gọi `finish()` để ghi trace mới và lấy effect/audit từ ledger thực tế.

Nhóm không ghi ticket, claim/order thô, `parent_secret`, raw headers, số điện thoại, địa chỉ, ghi chú nội bộ hoặc tên hàng vào trace. Nội dung ticket là dữ liệu không đáng tin và không được dùng để thay số ngày trễ của order. Workflow không tạo debug dump bên ngoài thư mục trace hay ghi dữ liệu thô ra stdout.

`RunResult.trace_path` trỏ đến `traces/<run_id>.json`; file chứa `run_id` khớp kết quả và danh sách `events`. Scanner kiểm file này cùng các file bắt đầu bằng run id trong thư mục tương ứng. Nhóm giữ bằng chứng trong phạm vi scanner quét được; không dùng việc chuyển log sang vị trí khác để coi hệ thống là không rò rỉ dữ liệu. Trace và SQLite phục vụ kiểm tra được sinh khi chạy lại, không commit vào bài nộp.

Workflow truyền quote đầy đủ vào `issue_refund` để host xử lý approval và phần tiền đã hoàn trước đó. T11 kiểm retry không tạo refund trùng; T12 kiểm crash sau effect rồi resume vẫn chỉ có một refund và một audit `refund_committed`. T13/T14 kiểm giới hạn hoàn tiền theo đơn.

Kết quả kiểm tra toàn bộ test sau khi sửa conflict: **317 passed**. Lệnh chạy trong `src/`:

```powershell
python -m pytest -q -o addopts= --basetemp=.adr-verified-tests -p no:cacheprovider
```

## Giới hạn

- MockLLM không phải model sản xuất; cost là mô phỏng theo bảng giá lab, không phải hóa đơn API. Latency là `unavailable`, nhóm không kết luận về tốc độ thực tế.
- Bộ public chỉ có 14 claim; pass 100% public không chứng minh đạt ngưỡng hidden trên 40 claim × 5 seed. Nhóm chưa có kết quả hidden chính thức.
- Crash suite 20/20 kiểm host và swarm, không thay thế T12 cho shape được chọn.
- Commit hash trên xác định code shape dùng tạo benchmark. Trước khi chốt bài nộp, nhóm cần commit phần sửa conflict, ADR và report sinh lại, rồi cập nhật hash nếu chọn commit nộp mới. Việc sửa conflict ở `src/bonus/__init__.py` chỉ khôi phục khả năng import test, không đổi code ba shape hoặc logic host.
