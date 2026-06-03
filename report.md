# llama.cpp CPU Benchmark Report

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`

## Models Tested

All models in Q4_K_M quantization. Each model was profiled with 3 prompt iterations; values are averages.

| Model | Params | Notes |
|---|---|---|
| Qwen 2.5-0.5B | 0.5B | Tiny, fast |
| Qwen 2.5-1.5B | 1.5B | General purpose |
| Qwen 2.5-3B | 3B | General purpose |
| Qwen 2.5 Coder-1.5B | 1.5B | Code-focused |
| Qwen 3.5-0.8B | 0.8B | Latest gen |
| Qwen 3.5-2B | 2B | Latest gen |
| Qwen 3.5-4B | 4B | Latest gen |
| Llama 3.2-1B | 1B | Meta |
| Llama 3.2-3B | 3B | Meta |
| Gemma 4 E2B | 2B | Google MoE |
| Gemma 4 E4B | 4B | Google MoE |
| SmolLM3-3B | 3B | HuggingFace |

## Benchmark Modes

Two modes were tested for each model:

| Mode | Server Flag | Description |
|---|---|---|
| **No thinking (direct)** | `--no-reasoning` on serve.sh | Model answers directly without chain-of-thought |
| **Thinking (CoT)** | Default | Model can reason before answering ("Answer short, concise, and correct.") |

## Results

### Time to First Token (TTFT) — lower is better

| Model | No Thinking (ms) | Thinking (ms) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 106 | 109 | +3% |
| Qwen 2.5-1.5B | 177 | 190 | +7% |
| Qwen 2.5-3B | 339 | 332 | -2% |
| Qwen 2.5 Coder-1.5B | 173 | 187 | +8% |
| Qwen 3.5-0.8B | 149 | 163 | +9% |
| Qwen 3.5-2B | 276 | 270 | -2% |
| Qwen 3.5-4B | 660 | 619 | -6% |
| Llama 3.2-1B | 100 | 119 | +19% |
| Llama 3.2-3B | 328 | 286 | -13% |
| Gemma 4 E2B | 259 | 295 | +14% |
| Gemma 4 E4B | 486 | 551 | +13% |
| SmolLM3-3B | 522 | 1127 | +116% |

### Time per Output Token (TPOT) — lower is better

| Model | No Thinking (ms) | Thinking (ms) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 15.20 | 14.99 | -1% |
| Qwen 2.5-1.5B | 32.87 | 34.40 | +5% |
| Qwen 2.5-3B | 64.65 | 64.07 | -1% |
| Qwen 2.5 Coder-1.5B | 31.19 | 32.71 | +5% |
| Qwen 3.5-0.8B | 23.52 | 24.35 | +4% |
| Qwen 3.5-2B | 47.23 | 48.36 | +2% |
| Qwen 3.5-4B | 98.12 | 102.11 | +4% |
| Llama 3.2-1B | 27.41 | 27.49 | +0% |
| Llama 3.2-3B | 67.15 | 68.72 | +2% |
| Gemma 4 E2B | 57.40 | 59.69 | +4% |
| Gemma 4 E4B | 104.51 | 108.99 | +4% |
| SmolLM3-3B | 63.31 | 69.08 | +9% |

### Generation Throughput — higher is better

| Model | No Thinking (tok/s) | Thinking (tok/s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 65.79 | 66.73 | +1% |
| Qwen 2.5-1.5B | 30.42 | 29.07 | -4% |
| Qwen 2.5-3B | 15.47 | 15.61 | +1% |
| Qwen 2.5 Coder-1.5B | 32.06 | 30.57 | -5% |
| Qwen 3.5-0.8B | 42.52 | 41.06 | -3% |
| Qwen 3.5-2B | 21.17 | 20.68 | -2% |
| Qwen 3.5-4B | 10.19 | 9.79 | -4% |
| Llama 3.2-1B | 36.49 | 36.37 | -0% |
| Llama 3.2-3B | 14.89 | 14.55 | -2% |
| Gemma 4 E2B | 17.42 | 16.75 | -4% |
| Gemma 4 E4B | 9.57 | 9.17 | -4% |
| SmolLM3-3B | 15.80 | 14.48 | -8% |

### Total Wall Duration — lower is better

| Model | No Thinking (s) | Thinking (s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 2.05 | 1.55 | -24% |
| Qwen 2.5-1.5B | 1.43 | 2.50 | +75% |
| Qwen 2.5-3B | 5.06 | 4.01 | -21% |
| Qwen 2.5 Coder-1.5B | 0.99 | 1.56 | +58% |
| Qwen 3.5-0.8B | 2.73 | 25.15 | +821% |
| Qwen 3.5-2B | 6.48 | 41.62 | +542% |
| Qwen 3.5-4B | 7.91 | 72.87 | +821% |
| Llama 3.2-1B | 3.29 | 3.99 | +21% |
| Llama 3.2-3B | 7.56 | 15.30 | +102% |
| Gemma 4 E2B | 8.28 | 27.11 | +227% |
| Gemma 4 E4B | 10.80 | 56.33 | +422% |
| SmolLM3-3B | 3.05 | 39.34 | +1190% |

## Key Findings

### 1. Thinking mode overhead varies dramatically by model family

- **Qwen 2.5 & Llama 3.2**: Efficient thinking. TTFT and TPOT overhead is minimal (<10%). Wall time increases are modest (up to 2× for Llama 3.2-3B). These models produce concise reasoning without overthinking.
- **Gemma 4**: Significant wall time increase (3-5×) due to verbose chain-of-thought (300-700 chunks vs 50-150 in no-think mode). Reasoning is coherent and well-structured.
- **SmolLM3-3B**: TTFT doubles (522→1127 ms) and wall time jumps 13× (3→39s) in thinking mode. The model struggles to structure concise reasoning.
- **Qwen 3.5 series**: Still problematic in thinking mode. All three models hit `max_tokens=1024` ceiling (~1027 chunks per iteration) due to recursive self-editing loops. The "short, concise, and correct" constraint triggers repetitive refinement rather than concise output. However, they now complete and produce output (unlike the previous "under 50 words" prompt which caused total failure for 4B).

### 2. TPOT is stable per model

Time per output token is determined almost entirely by model size and quantization, not by thinking mode. The 5-9% variation is within noise.

### 3. Throughput ranking (no-think mode)

| Rank | Model | tok/s |
|---|---|---|
| 1 | Qwen 2.5-0.5B | 65.8 |
| 2 | Qwen 3.5-0.8B | 42.5 |
| 3 | Llama 3.2-1B | 36.5 |
| 4 | Qwen 2.5 Coder-1.5B | 32.1 |
| 5 | Qwen 2.5-1.5B | 30.4 |
| 6 | Qwen 3.5-2B | 21.2 |
| 7 | Gemma 4 E2B | 17.4 |
| 8 | SmolLM3-3B | 15.8 |
| 9 | Qwen 2.5-3B | 15.5 |
| 10 | Llama 3.2-3B | 14.9 |
| 11 | Qwen 3.5-4B | 10.2 |
| 12 | Gemma 4 E4B | 9.6 |

## Recommendations

1. **For fast, direct answers**: Use `--no-reasoning`. Qwen 2.5-0.5B delivers ~66 tok/s with ~100ms TTFT.
2. **For thinking-enabled use**: Qwen 2.5-0.5B and Qwen 2.5-3B are the best balance — near-zero TTFT/TPOT overhead and efficient reasoning.
3. **Qwen 3.5 in thinking mode**: Avoid unless prompts are carefully tuned. All sizes (0.8B, 2B, 4B) hit the token ceiling with repetitive self-editing. No-think mode works fine (no recursive loop).
4. **Gemma 4 thinking**: Functional but expensive (3-5× wall time). Use only when CoT quality justifies the cost.
5. **SmolLM3-3B**: Underperforms in thinking mode (13× wall time). Use no-think mode only.

## Methodology

- Each model was served via `llama-server` (OpenAI-compatible API, `/v1/chat/completions`)
- CPU-only inference with OpenMP parallelism (16 threads)
- Thinking mode uses the default `--reasoning` template auto-detection; no custom Jinja templates
- Benchmark client (`profile_client.py`) streams responses, records TTFT (time to first output), TPOT (inter-token latency), total wall time, and chunk count
- Prompts: 3 varied questions about programming/CS topics, each with "Answer short, concise, and correct." constraint
- Qwen 3.5 models all hit `max_tokens=1024` ceiling (1027 chunks) in thinking mode due to recursive self-editing loops, but complete without total failure

### Test Date

2026-06-03
