# llama.cpp CPU Benchmark Report

**Hardware:** Intel i7-10700 (8C/16T, 2.9-4.8 GHz), 64GB RAM
**llama.cpp:** commit `4da6370`, OpenMP 8 threads, context 8192
**Quantization:** Q4_K_M (unless otherwise noted)
**Date:** June 2026

## Nothink Mode (no reasoning)

| Rank | Model | Params | Decode (tok/s) | Prompt (tok/s) |
|------|-------|--------|---------------|---------------|
| 1 | qwen2.5-0.5b | 0.5B | 49.9 | 305.0 |
| 2 | qwen3.5-0.8b | 0.8B | 45.8 | 236.9 |
| 3 | llama3.2-1b | 1B | 37.7 | 188.6 |
| 4 | qwen2.5-coder-1.5b | 1.5B | 30.6 | 157.3 |
| 5 | qwen2.5-1.5b | 1.5B | 30.1 | 157.0 |
| 6 | deepseek-r1-1.5b | 1.5B | 27.7 | 147.7 |
| 7 | qwen3.5-2b | 2B | 22.4 | 114.4 |
| 8 | gemma4-qat-e2b | 2.3B | 19.2 | 93.2 |
| 9 | gemma4-e2b | 2.3B | 18.2 | 96.2 |
| 10 | gemma2-2b | 2B | 16.7 | 97.0 |
| 11 | qwen2.5-3b | 3B | 16.1 | 81.5 |
| 12 | smollm3-3b | 3B | 15.9 | 81.4 |
| 13 | phi4-mini | 3.8B | 12.7 | 57.4 |
| 14 | gemma4-qat-26b-a4b | 26B (MoE, ~3.8B) | 11.9 | 45.9 |
| 15 | qwen3.6-35b-a3b | 35B (MoE, ~3B) | 10.4 | 40.1 |
| 16 | qwen3.5-4b | 4B | 10.3 | 44.0 |
| 17 | gemma4-qat-e4b | 4.5B | 10.3 | 48.2 |
| 18 | gemma4-e4b | 4.5B | 9.7 | 49.0 |
| 19 | gemma4-qat-12b | 12B | 4.4 | 18.2 |
| 20 | qwen3.6-27b | 27B | 1.9 | 7.5 |
| 21 | gemma4-qat-31b | 31B | 1.8 | 6.7 |

## Think Mode (reasoning enabled)

| Rank | Model | Params | Decode (tok/s) | Prompt (tok/s) |
|------|-------|--------|---------------|---------------|
| 1 | qwen2.5-0.5b | 0.5B | 57.9 | 293.2 |
| 2 | qwen3.5-0.8b | 0.8B | 41.5 | 227.3 |
| 3 | llama3.2-1b | 1B | 37.7 | 200.0 |
| 4 | qwen2.5-coder-1.5b | 1.5B | 31.0 | 160.2 |
| 5 | qwen2.5-1.5b | 1.5B | 30.4 | 145.6 |
| 6 | deepseek-r1-1.5b | 1.5B | 27.7 | 148.6 |
| 7 | qwen3.5-2b | 2B | 21.5 | 112.2 |
| 8 | gemma4-qat-e2b | 2.3B | 18.9 | 89.5 |
| 9 | gemma4-e2b | 2.3B | 17.9 | 87.9 |
| 10 | gemma2-2b | 2B | 16.6 | 93.0 |
| 11 | qwen2.5-3b | 3B | 16.1 | 78.8 |
| 12 | smollm3-3b | 3B | 15.4 | 85.9 |
| 13 | phi4-mini | 3.8B | 12.8 | 60.5 |
| 14 | gemma4-qat-26b-a4b | 26B (MoE, ~3.8B) | 11.4 | 41.3 |
| 15 | qwen3.6-35b-a3b | 35B (MoE, ~3B) | 10.2 | 38.9 |
| 16 | gemma4-qat-e4b | 4.5B | 10.1 | 45.6 |
| 17 | qwen3.5-4b | 4B | 9.9 | 44.7 |
| 18 | gemma4-e4b | 4.5B | 9.5 | 45.0 |
| 19 | gemma4-qat-12b | 12B | 4.2 | 16.8 |
| 20 | qwen3.6-27b | 27B | 1.9 | 7.6 |
| 21 | gemma4-qat-31b | 31B | 1.7 | 6.0 |

## Notes

- **QAT vs non-QAT:** gemma4-qat variants use Q4_0 quantization (quantization-aware trained), while standard gemma4 variants use Q4_K_M. QAT models are slightly faster on CPU at comparable sizes.
- **MoE advantage:** gemma4-qat-26b-a4b (26B total, ~3.8B active) runs at 11.9 tok/s — faster than many smaller dense models. qwen3.6-35b-a3b (35B total, ~3B active) also benefits at 10.4 tok/s.
- **Metrics:** All timings from server-side `predicted_per_second` and `prompt_per_second`. 10 questions per model, ranked by decode speed.

## Key Observations

1. **qwen2.5-0.5b dominates** at 49.9 tok/s nothink / 57.9 tok/s think — 28x faster than the slowest model (gemma4-qat-31b at 1.8 tok/s).
2. **Decode speeds are 3-9x lower than GPU** — most models 7-9x, large MoE/memory-bound models 3-4x. E.g., qwen2.5-0.5b: 49.9 tok/s CPU vs 427.4 tok/s GPU (8.6x); qwen3.6-35b-a3b: 10.4 tok/s CPU vs 29.0 tok/s GPU (2.8x).
3. **Think vs nothink decode speeds are nearly identical** — thinking just adds more output tokens at the same tok/s rate.
4. **qwen3.5 models loop in think mode** — wall time explodes (e.g., qwen3.5-2b: 6.3s nothink vs 174s think). Use `--no-reasoning` on CPU.
5. **MoE models punch above their weight** — gemma4-qat-26b-a4b and qwen3.6-35b-a3b outperform smaller dense models.
6. **gemma4-qat-31b and qwen3.6-27b** are batch/offline only at ~1.7-1.9 tok/s.
7. **Context window scaling on CPU** is primarily bound by system memory (RAM) bandwidth. Although the models natively support 128K–262K context lengths, processing long contexts on CPU triggers a massive TTFT (Time to First Token) prefill latency penalty. For CPU deployment, it is recommended to keep active context (`-c`) under 8,192 tokens for interactive workloads, keeping larger context sizes strictly for offline batch processing.

