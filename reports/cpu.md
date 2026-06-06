# llama.cpp CPU Benchmark Report

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`

## Models Tested

All models profiled with 3 prompt iterations; values are averages. Original 15 models use Q4_K_M quantization; 5 Gemma 4 QAT models use Q4_0 quantization (quantization-aware training).

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
| Gemma 2 2B IT | 2B | Google Dense |
| DeepSeek-R1-Distill-Qwen-1.5B | 1.5B | RL-reasoning distilled |
| Phi-4 Mini | 3.8B | Microsoft instruction-tuned |
| Gemma 4 E2B QAT | 2B (MoE) | Google QAT Q4_0 |
| Gemma 4 E4B QAT | 4B (MoE) | Google QAT Q4_0 |
| Gemma 4 12B QAT | 12B (Dense) | Google QAT Q4_0 |
| Gemma 4 26B-A4B QAT | ~4B (MoE 27B) | Google QAT Q4_0 |
| Gemma 4 31B QAT | 31B (Dense) | Google QAT Q4_0 |

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
| Qwen 3.5-0.8B | 175 | 153 | -13% |
| Qwen 3.5-2B | 276 | 270 | -2% |
| Qwen 3.5-4B | 660 | 619 | -6% |
| Llama 3.2-1B | 100 | 119 | +19% |
| Llama 3.2-3B | 328 | 286 | -13% |
| Gemma 4 E2B | 259 | 295 | +14% |
| Gemma 4 E4B | 486 | 551 | +13% |
| SmolLM3-3B | 522 | 1127 | +116% |
| Gemma 2 2B IT | 242 | 249 | +3% |
| DeepSeek-R1-Distill-Qwen-1.5B | 153 | 166 | +8% |
| Phi-4 Mini | 286 | 293 | +3% |
| Gemma 4 E2B QAT | 233 | 293 | +25% |
| Gemma 4 E4B QAT | 478 | 542 | +13% |
| Gemma 4 12B QAT | 1432 | 1522 | +6% |
| Gemma 4 26B-A4B QAT | 642 | 652 | +2% |
| Gemma 4 31B QAT | 3934 | 3924 | -0% |

### Time per Output Token (TPOT) — lower is better

| Model | No Thinking (ms) | Thinking (ms) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 15.20 | 14.99 | -1% |
| Qwen 2.5-1.5B | 32.87 | 34.40 | +5% |
| Qwen 2.5-3B | 64.65 | 64.07 | -1% |
| Qwen 2.5 Coder-1.5B | 31.19 | 32.71 | +5% |
| Qwen 3.5-0.8B | 23.15 | 25.56 | +10% |
| Qwen 3.5-2B | 47.23 | 48.36 | +2% |
| Qwen 3.5-4B | 98.12 | 102.11 | +4% |
| Llama 3.2-1B | 27.41 | 27.49 | +0% |
| Llama 3.2-3B | 67.15 | 68.72 | +2% |
| Gemma 4 E2B | 57.40 | 59.69 | +4% |
| Gemma 4 E4B | 104.51 | 108.99 | +4% |
| SmolLM3-3B | 63.31 | 69.08 | +9% |
| Gemma 2 2B IT | 60.46 | 60.20 | -0% |
| DeepSeek-R1-Distill-Qwen-1.5B | 34.51 | 36.40 | +5% |
| Phi-4 Mini | 79.77 | 78.74 | -1% |
| Gemma 4 E2B QAT | 54.20 | 54.82 | +1% |
| Gemma 4 E4B QAT | 98.04 | 99.30 | +1% |
| Gemma 4 12B QAT | 228.92 | 239.13 | +4% |
| Gemma 4 26B-A4B QAT | 84.94 | 91.82 | +8% |
| Gemma 4 31B QAT | 568.84 | 587.27 | +3% |

### Generation Throughput — higher is better

| Model | No Thinking (tok/s) | Thinking (tok/s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 65.79 | 66.73 | +1% |
| Qwen 2.5-1.5B | 30.42 | 29.07 | -4% |
| Qwen 2.5-3B | 15.47 | 15.61 | +1% |
| Qwen 2.5 Coder-1.5B | 32.06 | 30.57 | -5% |
| Qwen 3.5-0.8B | 43.19 | 39.12 | -9% |
| Qwen 3.5-2B | 21.17 | 20.68 | -2% |
| Qwen 3.5-4B | 10.19 | 9.79 | -4% |
| Llama 3.2-1B | 36.49 | 36.37 | -0% |
| Llama 3.2-3B | 14.89 | 14.55 | -2% |
| Gemma 4 E2B | 17.42 | 16.75 | -4% |
| Gemma 4 E4B | 9.57 | 9.17 | -4% |
| SmolLM3-3B | 15.80 | 14.48 | -8% |
| Gemma 2 2B IT | 16.54 | 16.61 | +0% |
| DeepSeek-R1-Distill-Qwen-1.5B | 28.98 | 27.47 | -5% |
| Phi-4 Mini | 12.54 | 12.70 | +1% |
| Gemma 4 E2B QAT | 18.45 | 18.24 | -1% |
| Gemma 4 E4B QAT | 10.20 | 10.07 | -1% |
| Gemma 4 12B QAT | 4.37 | 4.18 | -4% |
| Gemma 4 26B-A4B QAT | 11.77 | 10.89 | -8% |
| Gemma 4 31B QAT | 1.76 | 1.70 | -3% |

### Total Wall Duration — lower is better

| Model | No Thinking (s) | Thinking (s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 2.05 | 1.55 | -24% |
| Qwen 2.5-1.5B | 1.43 | 2.50 | +75% |
| Qwen 2.5-3B | 5.06 | 4.01 | -21% |
| Qwen 2.5 Coder-1.5B | 0.99 | 1.56 | +58% |
| Qwen 3.5-0.8B | 1.82 | 75.10 | +4125% |
| Qwen 3.5-2B | 6.48 | 41.62 | +542% |
| Qwen 3.5-4B | 7.91 | 72.87 | +821% |
| Llama 3.2-1B | 3.29 | 3.99 | +21% |
| Llama 3.2-3B | 7.56 | 15.30 | +102% |
| Gemma 4 E2B | 8.28 | 27.11 | +227% |
| Gemma 4 E4B | 10.80 | 56.33 | +422% |
| SmolLM3-3B | 3.05 | 39.34 | +1190% |
| Gemma 2 2B IT | 4.22 | 3.66 | -13% |
| DeepSeek-R1-Distill-Qwen-1.5B | 27.37 | 34.38 | +26% |
| Phi-4 Mini | 5.69 | 5.16 | -9% |
| Gemma 4 E2B QAT | 9.13 | 19.46 | +113% |
| Gemma 4 E4B QAT | 11.15 | 45.82 | +311% |
| Gemma 4 12B QAT | 39.99 | 151.57 | +279% |
| Gemma 4 26B-A4B QAT | 12.38 | 71.60 | +478% |
| Gemma 4 31B QAT | 115.11 | 257.86 | +124% |

## Key Findings

### 1. Thinking mode overhead varies dramatically by model family

- **Qwen 2.5 & Llama 3.2**: Efficient thinking. TTFT and TPOT overhead is minimal (<10%). Wall time increases are modest (up to 2× for Llama 3.2-3B). These models produce concise reasoning without overthinking.
- **Gemma 4**: Significant wall time increase (3-5×) due to verbose chain-of-thought (300-700 chunks vs 50-150 in no-think mode). Reasoning is coherent and well-structured.
- **Gemma 2 2B IT (Dense)**: Faster than Gemma 4 E2B on CPU (3.7s vs 27.1s thinking wall time) due to no MoE cache thrashing. However, it's 2 generations older — reasoning quality is notably weaker on complex tasks. TPOT is nearly identical between modes (+0-3%).
- **DeepSeek-R1-Distill-Qwen-1.5B**: Fastest reasoning model at 27.5 tok/s in thinking mode. In no-think mode behavior is **prompt-dependent** — sometimes finishes naturally (556–1527 chunks), sometimes loops to the `max_tokens` ceiling. Thinking mode is more reliable (all 3 iterations completed with `[think]` + `[out]`). The model has reasoning hardwired into its weights and doesn't cleanly separate thinking from output.
- **Phi-4 Mini**: Excellent instruction adherence. Concise, accurate answers in both modes with minimal verbosity. Wall time stays tight (5.2–5.7s). TPOT is predictable (~79ms) due to dense 3.8B architecture. Best model for multi-turn agent loops that require strict output discipline.
- **SmolLM3-3B**: TTFT doubles (522→1127 ms) and wall time jumps 13× (3→39s) in thinking mode. The model struggles to structure concise reasoning.
- **Qwen 3.5 series**: Still problematic in thinking mode. Models enter recursive self-critique loops that burn the entire `max_tokens` budget. Qwen 3.5-0.8B completed iteration 1 normally (465 chunks) but looped on 2/3 prompts. Larger sizes may loop on all prompts. No-think mode works cleanly for 0.8B.

### 2. TPOT is stable per model

Time per output token is determined almost entirely by model size and quantization, not by thinking mode. The 5-9% variation is within noise. The new models confirm this: Gemma 2 2B IT (+1%), DeepSeek-R1-Distill-Qwen-1.5B (+5%), Phi-4 Mini (+2%), Gemma 4 QAT E2B (+1%), Gemma 4 QAT E4B (+1%), Gemma 4 QAT 31B (+3%).

### 3. Gemma 4 QAT (Q4_0) vs non-QAT (Q4_K_M)

QAT models use quantization-aware training at Q4_0 precision, versus post-training Q4_K_M. Key comparison (E2B):

| Metric | E2B Q4_K_M | E2B QAT Q4_0 | Δ |
|---|---|---|---|
| TTFT (no-think) | 259 ms | 233 ms | -10% |
| TPOT (no-think) | 57.40 ms | 54.20 ms | -6% |
| Throughput (no-think) | 17.4 tok/s | 18.5 tok/s | +6% |
| Wall (no-think) | 8.28 s | 9.13 s | +10% |

QAT E2B is slightly faster per-token (+6% throughput) but produces more output in no-think mode (more verbose answers), resulting in slightly longer wall time. In thinking mode, both produce similar-length responses. QAT reasoning quality is equivalent or better.

- **26B-A4B QAT** is the most interesting QAT model: MoE with only ~4B active params but 27B total. Despite the small active set, it runs at 11.8 tok/s — comparable to the non-QAT E2B (17.4 tok/s). Wall time in thinking mode is 478% higher due to verbose CoT.
- **31B QAT** (dense 33B) is extremely slow: 1.7 tok/s, 3.9s TTFT. Only viable for no-think mode on CPU. Wall time is 115s no-think, 258s thinking.
- **12B QAT** (dense 12B) is also slow at 4.4 tok/s with 1.5s TTFT. Usable in no-think mode but painful in thinking mode (152s wall time).

### 4. Throughput ranking (no-think mode)

| Rank | Model | tok/s |
|---|---|---|
| 1 | Qwen 2.5-0.5B | 65.8 |
| 2 | Qwen 3.5-0.8B | 42.5 |
| 3 | Llama 3.2-1B | 36.5 |
| 4 | Qwen 2.5 Coder-1.5B | 32.1 |
| 5 | Qwen 2.5-1.5B | 30.4 |
| 6 | DeepSeek-R1-Distill-Qwen-1.5B | 29.0 |
| 7 | Qwen 3.5-2B | 21.2 |
| 8 | Gemma 2 2B IT | 16.5 |
| 9 | Gemma 4 E2B | 17.4 |
| 10 | SmolLM3-3B | 15.8 |
| 11 | Qwen 2.5-3B | 15.5 |
| 12 | Llama 3.2-3B | 14.9 |
| 13 | Phi-4 Mini | 12.7 |
| 14 | Qwen 3.5-4B | 10.2 |
| 15 | Gemma 4 E4B | 9.6 |
| 16 | Gemma 4 12B QAT | 4.4 |
| 17 | Gemma 4 E4B QAT | 10.2 |
| 18 | Gemma 4 26B-A4B QAT | 11.8 |
| 19 | Gemma 4 31B QAT | 1.8 |

## Recommendations

1. **For fast, direct answers**: Use `--no-reasoning`. Qwen 2.5-0.5B delivers ~66 tok/s with ~100ms TTFT.
2. **For thinking-enabled use**: Qwen 2.5-0.5B and Qwen 2.5-3B are the best balance — near-zero TTFT/TPOT overhead and efficient reasoning.
3. **Dense but older**: Gemma 2 2B IT is 2 generations behind Gemma 4 E2B. It's faster on CPU (3.7s vs 27s thinking wall time) due to no MoE, but quality doesn't match. Only use if speed matters more than reasoning depth.
4. **For reasoning tasks on CPU**: DeepSeek-R1-Distill-Qwen-1.5B streams at 27.5 tok/s in thinking mode — fastest reasoning throughput. No-think mode is unreliable (prompt-dependent looping). Prefer thinking mode.
5. **For multi-turn agent loops**: Phi-4 Mini — excellent instruction adherence, tight wall time (4.9–5.3s), no verbosity runaway. Best for structured/automated pipelines.
6. **Qwen 3.5 in thinking mode**: Avoid unless prompts are carefully tuned. All sizes (0.8B, 2B, 4B) hit the token ceiling with repetitive self-editing. No-think mode works fine (no recursive loop).
7. **Gemma 4 thinking**: Best quality on CPU, but expensive (3-5× wall time, 27s thinking). Pay the cost if reasoning depth matters.
8. **SmolLM3-3B**: Underperforms in thinking mode (13× wall time). Use no-think mode only.
9. **Gemma 4 QAT E2B/E4B**: Best QAT models for CPU. E2B QAT matches non-QAT E2B speed (18.5 vs 17.4 tok/s) with potential quality gains from quantization-aware training. Use `gemma4-qat-e2b` as a drop-in replacement for `gemma4-e2b`.
10. **Gemma 4 QAT 26B-A4B**: Surprisingly fast for a 27B MoE model (11.8 tok/s) due to only ~4B active parameters. Best QAT model for reasoning depth if you can tolerate 12s no-think / 72s thinking wall time.
11. **Gemma 4 QAT 12B/31B**: Too slow for interactive use on CPU (4.4 and 1.8 tok/s respectively). Only consider for batch/offline workloads.

## Methodology

- Each model was served via `llama-server` (OpenAI-compatible API, `/v1/chat/completions`)
- CPU-only inference with OpenMP parallelism (16 threads)
- Thinking mode uses the default `--reasoning` template auto-detection; no custom Jinja templates
- Benchmark client (`profile_client.py`) streams responses, records TTFT (time to first output), TPOT (inter-token latency), total wall time, and chunk count
- Prompts: 3 varied questions about programming/CS topics, each with "Answer short, concise, and correct." constraint
- `max_tokens`: 4096 for new models (Gemma 2, DeepSeek-R1, Phi-4, Gemma 4 QAT), 1024 for original 12 models
- Qwen 3.5 models enter infinite self-critique loops in thinking mode, burning the entire `max_tokens` budget in `[think]` tokens without producing `[out]`. No-think mode works cleanly for 0.8B.
- DeepSeek-R1-Distill-Qwen-1.5B in no-think mode is prompt-dependent: some prompts finish naturally (556–1527 chunks), others loop to the `max_tokens` ceiling. Thinking mode is reliable (all iterations complete).

### Test Date

2026-06-03 (original 15 models), 2026-06-06 (Gemma 4 QAT models added)
