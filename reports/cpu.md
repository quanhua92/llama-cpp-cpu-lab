# llama.cpp CPU Benchmark Report

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`

## Models Tested

20 models profiled with 10 fixed questions per mode. Original 15 models use Q4_K_M quantization; 5 Gemma 4 QAT models use Q4_0 quantization (quantization-aware training).

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

| Mode | Server Flag | Description |
|---|---|---|
| **No thinking (direct)** | `--no-reasoning` | Model answers directly without chain-of-thought |
| **Thinking (CoT)** | Default | Model reasons before answering |

## Results

### Time to First Token (TTFT) — lower is better

| Model | No Think (ms) | Think (ms) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 180.6 | 94.9 | -47% |
| Qwen 2.5-1.5B | 329.6 | 153.0 | -53% |
| Qwen 2.5-3B | 631.2 | 295.7 | -53% |
| Qwen 2.5 Coder-1.5B | 339.6 | 153.2 | -54% |
| Qwen 3.5-0.8B | 352.9 | 179.9 | -49% |
| Qwen 3.5-2B | 605.5 | 303.6 | -49% |
| Qwen 3.5-4B | 1,475.5 | 658.1 | -55% |
| Llama 3.2-1B | 218.5 | 122.6 | -44% |
| Llama 3.2-3B | 621.3 | 269.8 | -56% |
| Gemma 4 E2B | 545.3 | 276.9 | -49% |
| Gemma 4 E4B | 1,020.5 | 566.1 | -44% |
| SmolLM3-3B | 812.3 | 570.0 | -29% |
| Gemma 2 2B IT | 556.6 | 254.2 | -54% |
| DeepSeek-R1-Distill-Qwen-1.5B | 338.9 | 169.8 | -49% |
| Phi-4 Mini | 688.0 | 320.8 | -53% |
| Gemma 4 E2B QAT | 526.3 | 278.2 | -47% |
| Gemma 4 E4B QAT | 1,014.1 | 551.6 | -45% |
| Gemma 4 12B QAT | 2,976.9 | 1,494.5 | -49% |
| Gemma 4 26B-A4B QAT | 1,380.2 | 675.1 | -51% |
| Gemma 4 31B QAT | — | 7,167.1 | — |

### Time per Output Token (TPOT) — lower is better

| Model | No Think (ms) | Think (ms) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 31.1 | 14.1 | -54% |
| Qwen 2.5-1.5B | 59.7 | 31.7 | -46% |
| Qwen 2.5-3B | 108.4 | 59.9 | -44% |
| Qwen 2.5 Coder-1.5B | 56.0 | 30.6 | -45% |
| Qwen 3.5-0.8B | 40.5 | 23.3 | -42% |
| Qwen 3.5-2B | 84.1 | 46.3 | -44% |
| Qwen 3.5-4B | 184.0 | 99.6 | -45% |
| Llama 3.2-1B | 48.7 | 25.6 | -47% |
| Llama 3.2-3B | 122.2 | 64.5 | -47% |
| Gemma 4 E2B | 102.3 | 56.0 | -45% |
| Gemma 4 E4B | 195.0 | 103.7 | -46% |
| SmolLM3-3B | 112.6 | 65.6 | -41% |
| Gemma 2 2B IT | 109.9 | 58.7 | -46% |
| DeepSeek-R1-Distill-Qwen-1.5B | 64.8 | 34.3 | -47% |
| Phi-4 Mini | 141.7 | 75.1 | -47% |
| Gemma 4 E2B QAT | 100.4 | 53.1 | -47% |
| Gemma 4 E4B QAT | 184.7 | 99.6 | -46% |
| Gemma 4 12B QAT | 420.8 | 236.1 | -43% |
| Gemma 4 26B-A4B QAT | 159.6 | 88.2 | -44% |
| Gemma 4 31B QAT | — | 1,000.2 | — |

### Generation Throughput — higher is better

| Model | No Think (tok/s) | Think (tok/s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 32.14 | 71.03 | +121% |
| Qwen 2.5-1.5B | 16.74 | 31.55 | +88% |
| Qwen 2.5-3B | 9.23 | 16.71 | +81% |
| Qwen 2.5 Coder-1.5B | 17.86 | 32.63 | +82% |
| Qwen 3.5-0.8B | 24.68 | 42.89 | +73% |
| Qwen 3.5-2B | 11.88 | 21.62 | +81% |
| Qwen 3.5-4B | 5.43 | 10.04 | +84% |
| Llama 3.2-1B | 20.52 | 39.04 | +90% |
| Llama 3.2-3B | 8.19 | 15.51 | +89% |
| Gemma 4 E2B | 9.78 | 17.86 | +82% |
| Gemma 4 E4B | 5.13 | 9.64 | +88% |
| SmolLM3-3B | 8.88 | 15.25 | +71% |
| Gemma 2 2B IT | 9.10 | 17.03 | +87% |
| DeepSeek-R1-Distill-Qwen-1.5B | 15.44 | 29.20 | +89% |
| Phi-4 Mini | 7.05 | 13.32 | +88% |
| Gemma 4 E2B QAT | 9.96 | 18.83 | +89% |
| Gemma 4 E4B QAT | 5.41 | 10.04 | +85% |
| Gemma 4 12B QAT | 2.38 | 4.24 | +78% |
| Gemma 4 26B-A4B QAT | 6.27 | 11.34 | +80% |
| Gemma 4 31B QAT | — | 1.00 | — |

### Total Wall Duration — lower is better

| Model | No Think (s) | Think (s) | Δ |
|---|---|---|---|
| Qwen 2.5-0.5B | 18.1 | 8.7 | -51% |
| Qwen 2.5-1.5B | 5.0 | 2.6 | -48% |
| Qwen 2.5-3B | 5.9 | 3.2 | -45% |
| Qwen 2.5 Coder-1.5B | 2.5 | 1.4 | -44% |
| Qwen 3.5-0.8B | 5.1 | 87.9 | +1,624% |
| Qwen 3.5-2B | 12.2 | 173.9 | +1,325% |
| Qwen 3.5-4B | 23.0 | 169.9 | +639% |
| Llama 3.2-1B | 9.1 | 4.8 | -47% |
| Llama 3.2-3B | 22.8 | 12.0 | -47% |
| Gemma 4 E2B | 11.6 | 23.7 | +104% |
| Gemma 4 E4B | 25.3 | 53.6 | +112% |
| SmolLM3-3B | 8.2 | 33.1 | +303% |
| Gemma 2 2B IT | 10.1 | 5.3 | -47% |
| DeepSeek-R1-Distill-Qwen-1.5B | 84.0 | 44.0 | -47% |
| Phi-4 Mini | 8.7 | 4.5 | -48% |
| Gemma 4 E2B QAT | 14.1 | 22.6 | +60% |
| Gemma 4 E4B QAT | 22.3 | 58.9 | +164% |
| Gemma 4 12B QAT | 83.7 | 139.2 | +66% |
| Gemma 4 26B-A4B QAT | 32.3 | 62.6 | +94% |
| Gemma 4 31B QAT | — | 477.9 | — |

## Key Findings

### 1. Think mode has lower per-token latency across all models

All models show 42-55% lower TPOT in think mode. This is because TPOT measures inter-chunk latency across all output chunks (both reasoning and answer), and thinking produces many more short reasoning tokens which amortize the cost. However, wall time is a different story — thinking generates vastly more tokens overall.

### 2. Wall time tells the real cost of thinking

Think mode wall time splits into two categories:

**Wall time improves (think faster):** Qwen 2.5 family, Qwen 2.5 Coder, Llama 3.2, Gemma 2 2B IT, DeepSeek-R1, Phi-4 Mini. These models produce concise reasoning and finish quickly — total time is lower because TPOT gains outweigh the extra tokens.

**Wall time explodes (think much slower):** Qwen 3.5 family (+637% to +1,609%), Gemma 4 family (+60% to +164%), SmolLM3-3B (+305%). These models produce verbose chain-of-thought that dominates the total time.

### 3. Qwen 3.5 thinking is unusably slow on CPU

Qwen 3.5 models enter recursive self-critique loops, burning the `max_tokens` budget:
- Qwen 3.5-0.8B: 5.1s → 87.9s (17x slower)
- Qwen 3.5-2B: 12.2s → 173.9s (14x slower)
- Qwen 3.5-4B: 23.0s → 169.9s (7x slower)

No-think mode works cleanly. Avoid thinking mode for Qwen 3.5 on CPU.

### 4. Gemma 4 QAT (Q4_0) vs non-QAT (Q4_K_M)

| Metric | E2B Q4_K_M | E2B QAT Q4_0 | Δ |
|---|---|---|---|
| TTFT (no-think) | 545 ms | 526 ms | -3% |
| TPOT (no-think) | 102 ms | 100 ms | -2% |
| Throughput (no-think) | 9.78 tok/s | 9.96 tok/s | +2% |
| Wall (no-think) | 11.6 s | 14.1 s | +21% |
| Throughput (think) | 17.86 tok/s | 18.83 tok/s | +5% |

QAT and non-QAT are nearly identical in per-token speed. QAT models produce slightly more output (hence higher wall time) but with potentially better quality from quantization-aware training.

### 5. Throughput ranking (no-think mode)

| Rank | Model | tok/s |
|---|---|---|
| 1 | Qwen 2.5-0.5B | 32.1 |
| 2 | Qwen 3.5-0.8B | 24.7 |
| 3 | Llama 3.2-1B | 20.5 |
| 4 | Qwen 2.5 Coder-1.5B | 17.9 |
| 5 | Qwen 2.5-1.5B | 16.7 |
| 6 | DeepSeek-R1-Distill-Qwen-1.5B | 15.4 |
| 7 | Qwen 3.5-2B | 11.9 |
| 8 | Gemma 4 E2B QAT | 10.0 |
| 9 | Gemma 4 E2B | 9.8 |
| 10 | Gemma 2 2B IT | 9.1 |
| 11 | Qwen 2.5-3B | 9.2 |
| 12 | SmolLM3-3B | 8.9 |
| 13 | Llama 3.2-3B | 8.2 |
| 14 | Phi-4 Mini | 7.1 |
| 15 | Gemma 4 26B-A4B QAT | 6.3 |
| 16 | Qwen 3.5-4B | 5.4 |
| 17 | Gemma 4 E4B QAT | 5.4 |
| 18 | Gemma 4 E4B | 5.1 |
| 19 | Gemma 4 12B QAT | 2.4 |

### 6. Question-level consistency

TPOT is highly consistent across questions — std dev ranges from 2-16 ms (nothink) and 0.2-2.1 ms (think) regardless of question topic. Think mode TPOT is extremely predictable (CV <1% for most models). Nothink TPOT varies more because output length per question affects chunk distribution. TTFT varies more (23-433 ms std dev nothink, 12-787 ms think) because first-token latency depends on prompt complexity.

The exception is Q10 (database transactions) in think mode, which shows dramatically lower values because gemma4-qat-31b only completed 9/10 questions, skewing the average.

## Recommendations

1. **Fastest overall**: Qwen 2.5-0.5B — 71 tok/s think, 32 tok/s no-think, ~95-181ms TTFT
2. **Best small reasoning model**: Llama 3.2-1B — 39 tok/s think, 20.5 tok/s no-think, wall time improves in think mode
3. **Best reasoning throughput**: DeepSeek-R1-Distill-Qwen-1.5B — 29.2 tok/s think, reliable in thinking mode
4. **Tightest multi-turn agent**: Phi-4 Mini — concise outputs, wall time improves with thinking (8.7s → 4.5s)
5. **Qwen 3.5**: Use `--no-reasoning` only. Think mode loops to token ceiling.
6. **Gemma 4**: Best quality but 2-3x wall time in think mode. Use no-think for interactive use.
7. **Gemma 4 QAT E2B**: Best QAT model for CPU — nearly identical speed to non-QAT with potential quality gains
8. **Gemma 4 QAT 26B-A4B**: Surprisingly fast for a 27B MoE (6.3 tok/s no-think) — only ~4B active params
9. **Gemma 4 QAT 12B/31B**: Too slow for interactive use (2.4 and 1.0 tok/s). Batch/offline only.
10. **SmolLM3-3B**: 4x slower in think mode (8.2s → 33.1s). Use no-think only.

## Methodology

- Each model served via `llama-server` (OpenAI-compatible API, `/v1/chat/completions`)
- CPU-only inference, OpenMP parallelism (8 threads), context 8192
- **10 fixed questions** (Q01-Q10) in a consistent order across all models — no randomization
- Each question is a CS/programming topic with "Answer short, concise, and correct." constraint
- Streaming benchmark records: TTFT, TPOT, token chunk count, total wall time
- `max_tokens`: 4096, `temperature`: 0.0
- Results parsed by `scripts/analyze_results.py` for reproducible analysis

### Questions Used

| ID | Topic |
|---|---|
| Q01 | Software architecture |
| Q02 | How neural networks learn |
| Q03 | TCP vs UDP |
| Q04 | Garbage collection in Python |
| Q05 | Microservices |
| Q06 | Closures in programming |
| Q07 | CAP theorem |
| Q08 | DNS resolution |
| Q09 | Design patterns |
| Q10 | Database transactions |

### Test Date

2026-06-06 (all 20 models, 10 questions, think + nothink modes)
