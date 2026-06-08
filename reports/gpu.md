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

## Key Observations

1. **qwen2.5-0.5b dominates** at 427.4 tok/s nothink / 426.9 tok/s think — which is over 60x faster than the slowest models.
2. **GPU speeds are 3-9x higher than CPU** — for example, qwen2.5-0.5b: 427.4 tok/s GPU vs 49.9 tok/s CPU (8.6x); qwen3.6-35b-a3b: 29.0 tok/s GPU vs 10.4 tok/s CPU (2.8x).
3. **MoE models offer excellent GPU throughput** — `gemma4-qat-26b-a4b` (14 GB) runs at 87.9 tok/s because it fits entirely in VRAM, which is faster than dense 4B/4.5B models (e.g., `qwen3.5-4b` at 79.9 tok/s and `gemma4-e4b` at 75.3 tok/s).
4. **The VRAM Cliff drops speeds drastically** — models above 15 GB like `qwen3.6-35b-a3b` (29.0 tok/s) and `gemma4-qat-31b` (7.1 tok/s) must partially offload layers, dropping throughput significantly.

## Notes

- **GPU offload:** Models up to ~16 GB use full GPU offload (`-ngl 99`). Larger models use partial offload:
  - `gemma4-qat-31b` (17 GB) and `qwen3.6-27b` (16 GB): `--ngl 40`
  - `qwen3.6-35b-a3b` (21 GB): `--ngl 20` (MoE — only ~3B active params, still 29 tok/s)
  - `gemma4-qat-26b-a4b` (14 GB): `--ngl 99` (MoE — only ~3.8B active params)
- **QAT vs non-QAT:** gemma4-qat variants use Q4_0 quantization (the quantization-aware trained format), while standard gemma4 variants use Q4_K_M.
- **Metrics:** All timings from server-side `predicted_per_second` and `prompt_per_second`. 10 questions per model, 0 failures across all models.
- **Think mode:** Enables reasoning/thinking tokens. Decode speeds are nearly identical to nothink for most models — thinking models (deepseek-r1) produce much longer output but at the same tok/s rate.

## Key Insights on GPU Offload & MoE Trade-Offs

### 1. The VRAM Cliff & Partial Offloading
On a 16 GB VRAM consumer card (such as the RTX 4060 Ti in this workstation), there is a steep performance cliff once a model exceeds the VRAM limit:
*   **Full Offload (`-ngl 99`):** Models like `gemma4-qat-26b-a4b` (14 GB) fit entirely in VRAM, achieving a high decode throughput of **`87.9 tok/s`**.
*   **Partial Offload:** Once a model's size exceeds ~15 GB, llama.cpp must split layers between the GPU and host CPU/RAM, introducing PCIe bandwidth bottlenecks:
    *   `qwen3.6-35b-a3b` (21 GB) runs with `--ngl 20` at **`29.0 tok/s`** (3x speed penalty).
    *   `gemma4-qat-31b` (17 GB) runs with `--ngl 40` at **`7.1 tok/s`** (12x speed penalty!).

### 2. MoE vs. Dense Performance Under VRAM Constraints
Mixture of Experts (MoE) models offer substantial speed advantages over dense models of similar size when VRAM is constrained:
*   **At 29 tok/s**, `qwen3.6-35b-a3b` (MoE with ~3B active params) is **4x faster** than `gemma4-qat-31b` (dense 31B model running at 7.1 tok/s) despite both requiring partial offloading. This is because MoE models process only a fraction of the compute (~3B vs 31B parameters) per token.
*   **Fits-in-VRAM MoE (`gemma4-qat-26b-a4b`):** With ~3.8B active parameters, this model fits entirely in 16 GB VRAM and generates at **`87.9 tok/s`**, offering a near-perfect balance of high reasoning capability and interactive-grade speed.

### 3. KV Cache & Context Window VRAM Overhead
*   The native context windows (256K for Gemma 4, 262K for Qwen 3.6) require significant memory for the KV cache.
*   For models that barely fit in VRAM (like `gemma4-qat-26b-a4b` at 14.4 GB), running long context sessions (e.g., above 16K–32K context) will consume the remaining VRAM overhead and trigger out-of-memory (OOM) errors. In such cases, developers must either restrict the context length (`-c`) or offload some layers to CPU to free VRAM for the KV cache.

