# Gemma 4 Q4_K_M vs QAT Q4_0 Comparison

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`
> Q4_K_M = post-training quantization | QAT Q4_0 = quantization-aware training
> Bold = faster value in each category.

## TTFT (ms) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 259 | **233** | 295 | **293** |
| E4B | 486 | **478** | 551 | **542** |

## TPOT (ms) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 57.40 | **54.20** | 59.69 | **54.82** |
| E4B | 104.51 | **98.04** | 108.99 | **99.30** |

## Throughput (tok/s) — higher is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 17.42 | **18.45** | 16.75 | **18.24** |
| E4B | 9.57 | **10.20** | 9.17 | **10.07** |

## Wall Duration (s) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | **8.28** | 9.13 | 27.11 | **19.46** |
| E4B | **10.80** | 11.15 | 56.33 | **45.82** |

## Key Takeaways

- **QAT Q4_0 wins per-token speed** (TPOT, throughput) and TTFT across all metrics and modes.
- **Q4_K_M wins wall time in no-think mode only** — QAT produces more verbose direct answers, increasing total output tokens.
- **QAT wins wall time in thinking mode** — it reasons more concisely, so despite similar per-token speed, it finishes faster.
- **QAT E2B thinking wall time is 19.5s vs 27.1s** for Q4_K_M — a 28% improvement.
- **QAT E4B thinking wall time is 45.8s vs 56.3s** — a 19% improvement.
- **Recommendation**: Use QAT Q4_0 as a drop-in replacement for Q4_K_M. Same or better speed with quantization-aware training benefits.

## Methodology

- Each model was profiled with 3 prompt iterations; values are averages.
- Q4_K_M models: `unsloth/gemma-4-E2B-it-GGUF` and `unsloth/gemma-4-E4B-it-GGUF`
- QAT Q4_0 models: `google/gemma-4-E2B-it-qat-q4_0-gguf` and `google/gemma-4-E4B-it-qat-q4_0-gguf`
- `max_tokens`: 4096 for all four models.
- Test date: 2026-06-06
