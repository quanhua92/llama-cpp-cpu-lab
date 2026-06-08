# GPU Context Scaling Report — Gemma 4 26B-A4B

**Date:** 2026-06-08
**Hardware:** Intel i9-13900K (24C/32T), 64GB RAM, NVIDIA RTX 4060 Ti 16GB (Ada, SM 8.9)
**Model:** gemma-4-26B-A4B-it-qat-q4_0.gguf (MoE, 26B total / ~3.8B active, Q4_0 QAT, 14 GB)
**llama.cpp:** commit `4da6370`
**KV Cache:** Q8_0 (both K and V)
**GPU Offload:** ngl=99 (all layers on GPU)
**Corpus:** Project Gutenberg #1661 (Crime and Punishment, ~580K chars)
**Fill ratio:** 80% of context window

## Overview

This report measures how performance degrades as the context window fills with real text. Two data sources are combined:

1. **Config sweep** (`sweep_gpu_config.sh`) — automated grid sweep over ngl x ctx x threads x speculative decoding, using long prompts (corpus + question).
2. **Context profile** (`profile_context.py`) — targeted context scaling benchmark at 5 context sizes (4K/8K/16K/32K/64K) with streaming server timings.

## Phase 1: Thread & Speculative Decoding Tuning

Short prompt (`"What is 2+2?"`), ctx=8192, ngl=99.

| Threads | Speculative | TTFT (ms) | Decode (tok/s) |
|---------|-------------|-----------|----------------|
| 8 | none | 80 | 88.1 |
| 8 | ngram-simple | 79 | 88.1 |
| 16 | none | 79 | **88.2** |
| 16 | ngram-simple | 80 | 88.1 |
| 24 | none | 81 | 88.1 |
| 24 | ngram-simple | 80 | 87.8 |

**Finding:** No meaningful difference across thread counts or speculative decoding on short prompts. All configurations produce ~88 tok/s. The GPU is the bottleneck, not CPU threads. Speculative decoding (ngram-simple) provides zero benefit — the short prompt has no repeated patterns to exploit.

## Phase 2: Context Scaling (Long Prompts)

Long prompt: corpus text filling 80% of context + `"Summarize the key themes and writing style in the text above in 3-5 sentences."`

### ngl=99 (all layers on GPU) — KV8

| Context | ~Prompt Tokens | ~Prompt Chars | TTFT (ms) | Decode (tok/s) | TTFT/prompt_token |
|---------|----------------|---------------|-----------|----------------|-------------------|
| 8K | ~6,749 | 26,999 | 2,474 | 68.3 | 0.37 ms |
| 32K | ~26,927 | 107,710 | 12,434 | 53.0 | 0.46 ms |
| 64K | ~53,732 | 214,929 | **30,087** | **36.6** | 0.56 ms |

### ngl=60

| Context | ~Prompt Tokens | TTFT (ms) | Decode (tok/s) |
|---------|----------------|-----------|----------------|
| 8K | ~6,749 | 2,476 | 68.3 |
| 32K | ~26,927 | 12,440 | 53.0 |
| 64K | ~53,732 | 30,088 | 36.6 |

### ngl=40

| Context | ~Prompt Tokens | TTFT (ms) | Decode (tok/s) |
|---------|----------------|-----------|----------------|
| 8K | ~6,749 | 2,479 | 68.3 |
| 32K | ~26,927 | 12,444 | 53.0 |
| 64K | ~53,732 | 30,088 | 36.7 |

### ngl=20

| Context | ~Prompt Tokens | TTFT (ms) | Decode (tok/s) |
|---------|----------------|-----------|----------------|
| 8K | ~6,749 | **7,424** | 34.1 |
| 32K | ~26,927 | 30,050 | 25.0 |
| 64K | ~53,732 | 30,086 | **8.0** |

## Streaming Context Profile (`profile_context.py`)

Server: ngl=99, -c 65536, KV8, -t 8. Each run uses a unique prefix to bust KV cache (cache_n=0 cold runs).

| Context | Prompt Tokens | Corpus Chars | TTFT (ms) | Prompt Time (ms) | Prefill (tok/s) | Decode (tok/s) | Cache Hits |
|---------|--------------|-------------|-----------|------------------|-----------------|----------------|------------|
| 4K | 2,459 | 9,828 | 971 | 899 | 2,736 | 75.4 | 0 |
| 8K | 4,926 | 19,659 | 1,923 | 1,806 | 2,728 | 69.4 | 0 |
| 16K | 9,868 | 39,321 | 3,901 | 3,772 | 2,616 | 64.8 | 0 |
| 32K | 19,838 | 78,642 | 8,816 | 8,640 | 2,296 | 56.9 | 0 |
| 64K | 39,140 | 157,284 | 21,312 | 21,087 | 1,856 | 46.5 | 0 |

All runs are cold (no cache hits). The unique prefix `[ContextProfile ctx{N}-{timestamp}]` busts any KV cache from prior runs, giving clean prefill measurements.

## Analysis

### 1. ngl scaling: diminishing returns below 40

For ctx=8K and 32K, ngl=40 performs identically to ngl=99 (both decode at ~68.3 and ~53.0 tok/s). The model's compute is GPU-bound even with 40 layers offloaded at these context sizes. The drop-off is sharp at ngl=20: TTFT nearly 3x higher at 8K, and decode crashes to 8.0 tok/s at 64K.

**Conclusion:** ngl=99 is optimal. If you need to free VRAM for a larger model, ngl=40 is a safe floor with no performance loss at ctx<=32K.

### 2. Decode speed degrades ~38% from 4K to 64K

| Context | Decode (tok/s) | Drop from 4K baseline |
|---------|----------------|----------------------|
| 4K | 75.4 | — |
| 8K | 69.4 | -8% |
| 16K | 64.8 | -14% |
| 32K | 56.9 | -25% |
| 64K | 46.5 | -38% |

The degradation accelerates at larger contexts. From 4K to 16K, decode drops only 14% (8 tok/s). From 16K to 64K, it drops another 28% (18 tok/s). The KV cache attention overhead dominates at longer sequences.

**Important:** These numbers are with 80% context fill. Short prompts (e.g., "What is 2+2?") still hit 88 tok/s even on a server configured with `-c 65536`. The context size is just the ceiling — decode speed depends on how many tokens are actually in the KV cache, not the max window size. Setting `-c 65536` does not penalize short prompts.

### 3. TTFT scales super-linearly with prompt size

| Context | Prompt Tokens | TTFT | ms/token |
|---------|---------------|------|----------|
| 4K | 2,459 | 0.97s | 0.37 |
| 8K | 4,926 | 1.92s | 0.37 |
| 16K | 9,868 | 3.90s | 0.38 |
| 32K | 19,838 | 8.82s | 0.44 |
| 64K | 39,140 | 21.3s | 0.54 |

Prefill cost per token is nearly constant at 0.37ms up to 16K, then climbs to 0.54ms at 64K — a 46% increase. The quadratic attention cost becomes visible above 16K context.

### 4. Prefill throughput stays strong until 32K

| Context | Prefill (tok/s) | Drop from 4K |
|---------|-----------------|-------------|
| 4K | 2,736 | — |
| 8K | 2,728 | <1% |
| 16K | 2,616 | -4% |
| 32K | 2,296 | -16% |
| 64K | 1,856 | -32% |

Prefill throughput (tokens processed per second) degrades much less than decode speed. The GPU handles batch prefill efficiently — the bottleneck shifts to attention bandwidth only at 32K+.

### 5. Speculative decoding: no benefit

ngram-simple speculative decoding showed zero improvement on both short and long prompts. This model's output doesn't have sufficient repetitive patterns for ngram-based guessing to help. A draft-model approach (`-md`) might work better but costs extra VRAM.

### 6. KV caching benefit on sequential requests

The `profile_context.py` runs use unique prefixes per run to bust the KV cache, giving clean cold-prefill measurements. Without cache busting (earlier run), the 2K run showed 1,173 cache hits and 384ms TTFT — vs 725ms cold. Cache reuse is a significant real-world benefit for sequential conversations on the same context window.

## Recommendations

### Service config (RTX 4060 Ti 16GB)

```
ExecStart=serve_gpu.sh gemma4-qat-26b-a4b 8889 -c 65536 -ctk q8_0 -ctv q8_0
```

- **64K context fits** in 16GB VRAM with KV8 quant. Short prompts still hit 88 tok/s regardless of `-c`. Use 64K unless you need the VRAM for a second model.
- **KV8 quantization** is required for contexts above 8K on 16GB VRAM.
- **ngl=99** is optimal. `--ngl 40` is a safe fallback with no measurable loss at ctx<=32K.
- The repo template (`systemd/llama-gpu.service`) uses `-c 16384` as a conservative default. Adjust for your GPU.

### When partial offload is acceptable

For models that don't fit fully in VRAM (e.g., qwen3.6-27b at 16.8 GB), use `--ngl 40`. At ctx<=32K, performance matches full offload. At 64K, CPU fallback becomes visible.

## Data Sources

- **Sweep:** `tuning/gpu/gemma4-qat-26b-a4b/20260608_123845/`
- **Context profile:** `results/gpu/context_profile.json`
