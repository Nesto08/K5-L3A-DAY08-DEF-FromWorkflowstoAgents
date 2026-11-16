# Bonus report: B1

- Topic + nguồn (tên, năm, slide): B1 · Investigator song song và critical path; Google Research 2026, *Towards a Science of Scaling Agent Systems*, slides 15, 24, 33, 41 (the source and claim as specified in `docs/bonus_topics.md`).
- CLAIM của nguồn (1 câu): In the evaluated setup, the source reports that multi-agent variants can lose 39–70% on sequential tasks; parallelism is useful when work can actually be split into independent tasks.
- BOUNDARY (model / dataset / setup): Synthetic LogiX-VN public set (14 claims × 5 seeds), deterministic MockLLM, and a hand-authored latency model. These measurements do not represent production or wall-clock latency.
- HYPOTHESIS trên LogiX: `lookup_order` and `lookup_policy` can run concurrently after the claim is read. Quote computation depends on both results; drafting and the host refund write remain sequential. Therefore parallel execution should reduce simulated critical path without changing correctness or simulated cost.
- Biến cố định / biến thay đổi: Fixed claims, world, seeds (`11,22,33,44,55`), MockLLM backend, tools, pricing, evaluator, and refund host. Both shapes make one draft call; changed only the scheduling of independent order and policy reads from serial to concurrent.
- Lệnh tái lập (copy-paste được):

  ```powershell
  python -m lab8.benchmark --shapes orchestrator,orchestrator_parallel --extra-shape orchestrator_parallel=bonus.orchestrator_parallel:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/bonus_b1_benchmark.json
  python -m bonus.critical_path --benchmark reports/bonus_b1_benchmark.json --cases data/public_claims.jsonl --world data/public_world_state.json --out reports/bonus_b1_latency.json
  python -m pytest -q tests/test_bonus_b1_parallel.py
  ```
- File report + run id: `src/reports/bonus_b1_benchmark.json`, `src/reports/bonus_b1_latency.json`; example run `R-orchestrator_parallel-C-001-s11`.

## Kết quả

Source: generated JSON reports above; each shape has 70 graded trials.

| Shape / schedule | Pass rate | pass^5 | Seed variance | Cost/success (simulated VND) | Critical-path mean | Critical-path p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Serial `orchestrator` | 1.000 (70/70) | 1.000 | 0.000000 | 37.37 | 258.686 ms | 287 ms |
| `orchestrator_parallel` | 1.000 (70/70) | 1.000 | 0.000000 | 37.37 | 218.943 ms | 245 ms |

The modeled mean path is 39.743 ms shorter (15.36%); the mean-path ratio is 1.1815×. P95 is 42 ms shorter. Both shapes have identical pass rate, pass^5, variance, model calls, tool calls, and simulated cost. All 70 trials per shape passed the benchmark evaluator, including its ledger/result/trace checks; this is public-set evidence, not a separate hidden-set safety certification.

The fixed base durations for a fully entitled path are 281 ms serial (`claim view → order → policy → quote → draft → refund`) and 239 ms when only the independent order/policy reads overlap, a modeled ratio of about 1.176×. The aggregate 1.1815× is close to that estimate. This is a deterministic critical-path calculation from `bonus/latency.yaml`, **not measured runtime**; no `sleep` is used. Quote depends on both order and policy, so only the two reads can overlap. The writer remains singular and runs after the quote and draft.

Focused tests: `python -m pytest -q tests/test_bonus_b1_parallel.py` → `10 passed`.

## Kết luận

The results support the limited hypothesis for this workflow: parallelizing the two independent read calls lowered modeled critical path while keeping public benchmark outcomes and simulated cost unchanged. It does not show real latency improvement: local SQLite reads may be so fast that thread-pool overhead outweighs the simulated benefit. The conclusion would change if a real deployment had different tool latencies, contention, remote calls, or dependencies that prevented order and policy reads from overlapping.

## Giới hạn

MockLLM is deterministic and has no real latency; tool/model durations and seed jitter are explicitly simulated in `src/bonus/latency.yaml`. The dataset is small and synthetic. Only two investigator reads are parallelized; quote, drafting, and refund writing remain on the critical path. No inference is made about hidden claims or production performance.
