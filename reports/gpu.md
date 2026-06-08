# llama.cpp GPU Benchmark Report

**Hardware:** Intel i9-13900K, 64GB RAM, NVIDIA RTX 4060 Ti 16GB (Ada, SM 8.9)
**llama.cpp:** commit `4da6370`
**Quantization:** Q4_K_M (unless otherwise noted)
**Date:** June 2026

## Nothink Mode (no reasoning)

| Rank | Model | Size | Decode (tok/s) | Prompt (tok/s) |
|------|-------|------|---------------|---------------|
| 1 | qwen2.5-0.5b | 469 MB | 427.4 | 3,787.9 |
| 2 | qwen3.5-0.8b | 508 MB | 295.1 | 1,801.9 |
| 3 | llama3.2-1b | 771 MB | 279.2 | 3,584.3 |
| 4 | qwen2.5-coder-1.5b | 1.1 GB | 218.9 | 2,585.5 |
| 5 | qwen2.5-1.5b | 1.1 GB | 217.6 | 2,577.4 |
| 6 | deepseek-r1-1.5b | 1.1 GB | 209.3 | 1,847.7 |
| 7 | qwen3.5-2b | 1.2 GB | 161.2 | 1,359.0 |
| 8 | gemma4-qat-e2b | 3.2 GB | 142.1 | 951.8 |
| 9 | gemma4-e2b | 2.9 GB | 138.1 | 682.0 |
| 10 | gemma2-2b | 1.6 GB | 127.3 | 1,165.2 |
| 11 | smollm3-3b | 1.8 GB | 123.8 | 2,072.2 |
| 12 | qwen2.5-3b | 2.0 GB | 123.3 | 1,561.1 |
| 13 | llama3.2-3b | 1.9 GB | 118.6 | 1,661.5 |
| 14 | phi4-mini | 2.4 GB | 99.0 | 1,233.6 |
| 15 | gemma4-qat-26b-a4b | 14 GB | 87.9 | 458.2 |
| 16 | qwen3.5-4b | 2.6 GB | 79.9 | 665.7 |
| 17 | gemma4-qat-e4b | 4.9 GB | 79.2 | 610.2 |
| 18 | gemma4-e4b | 4.7 GB | 75.3 | 478.1 |
| 19 | gemma4-qat-12b | 6.5 GB | 35.6 | 380.1 |
| 20 | qwen3.6-35b-a3b | 21 GB | 29.0 | 77.6 |
| 21 | gemma4-qat-31b | 17 GB | 7.1 | 27.4 |
| 22 | qwen3.6-27b | 16 GB | 7.0 | 23.3 |

## Think Mode (reasoning enabled)

| Rank | Model | Size | Decode (tok/s) | Prompt (tok/s) |
|------|-------|------|---------------|---------------|
| 1 | qwen2.5-0.5b | 469 MB | 426.9 | 3,875.9 |
| 2 | qwen3.5-0.8b | 508 MB | 285.0 | 1,663.9 |
| 3 | llama3.2-1b | 771 MB | 279.1 | 3,543.8 |
| 4 | qwen2.5-coder-1.5b | 1.1 GB | 219.4 | 2,581.5 |
| 5 | qwen2.5-1.5b | 1.1 GB | 217.6 | 2,567.3 |
| 6 | deepseek-r1-1.5b | 1.1 GB | 209.4 | 1,863.7 |
| 7 | qwen3.5-2b | 1.2 GB | 158.1 | 1,248.7 |
| 8 | gemma4-qat-e2b | 3.2 GB | 141.1 | 821.5 |
| 9 | gemma4-e2b | 2.9 GB | 134.0 | 557.2 |
| 10 | gemma2-2b | 1.6 GB | 127.5 | 1,163.3 |
| 11 | qwen2.5-3b | 2.0 GB | 122.9 | 1,550.8 |
| 12 | smollm3-3b | 1.8 GB | 120.1 | 2,686.8 |
| 13 | llama3.2-3b | 1.9 GB | 118.6 | 1,663.3 |
| 14 | phi4-mini | 2.4 GB | 98.9 | 1,240.0 |
| 15 | gemma4-qat-26b-a4b | 14 GB | 85.9 | 354.6 |
| 16 | qwen3.5-4b | 2.6 GB | 78.6 | 619.8 |
| 17 | gemma4-e4b | 4.7 GB | 74.5 | 410.0 |
| 18 | gemma4-qat-e4b | 4.9 GB | 63.2 | 412.7 |
| 19 | gemma4-qat-12b | 6.5 GB | 35.1 | 253.6 |
| 20 | qwen3.6-35b-a3b | 21 GB | 28.4 | 67.2 |
| 21 | gemma4-qat-31b | 17 GB | 7.0 | 25.3 |
| 22 | qwen3.6-27b | 16 GB | 6.9 | 22.3 |

## Notes

- **GPU offload:** Models up to ~16 GB use full GPU offload (`-ngl 99`). Larger models use partial offload:
  - `gemma4-qat-31b` (17 GB) and `qwen3.6-27b` (16 GB): `--ngl 40`
  - `qwen3.6-35b-a3b` (21 GB): `--ngl 20` (MoE — only ~3B active params, still 29 tok/s)
  - `gemma4-qat-26b-a4b` (14 GB): `--ngl 99` (MoE — only ~3.8B active params)
- **QAT vs non-QAT:** gemma4-qat variants use Q4_0 quantization (the quantization-aware trained format), while standard gemma4 variants use Q4_K_M.
- **Metrics:** All timings from server-side `predicted_per_second` and `prompt_per_second`. 10 questions per model, 0 failures across all models.
- **Think mode:** Enables reasoning/thinking tokens. Decode speeds are nearly identical to nothink for most models — thinking models (deepseek-r1) produce much longer output but at the same tok/s rate.
