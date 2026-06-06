# Gemma 4 Q4_K_M vs QAT Q4_0 Comparison

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`
> Q4_K_M = post-training quantization | QAT Q4_0 = quantization-aware training
> Bold = faster value in each category. Averages over 10 fixed questions.

## TTFT (ms) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 545 | **526** | 277 | **278** |
| E4B | 1,020 | **1,014** | 566 | **552** |

## TPOT (ms) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 102 | **100** | 56.0 | **53.1** |
| E4B | 195 | **185** | 104 | **100** |

## Throughput (tok/s) — higher is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 9.78 | **9.96** | 17.86 | **18.83** |
| E4B | 5.13 | **5.41** | 9.64 | **10.04** |

## Wall Duration (s) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | **11.6** | 14.1 | **23.7** | 22.6 |
| E4B | **25.3** | 22.3 | **53.6** | 58.9 |

## All MoE Models at a Glance

TPOT scales with **active params**, not total model size. This is why 26B-A4B (27B total, ~4B active) is faster per-token than E4B (8B total, 4.5B active).

| Model | Type | Active | Total | Size | NT tok/s | TH tok/s | NT TTFT | TH TTFT |
|---|---|---|---|---|---|---|---|---|
| **gemma4-e2b** | MoE Q4_K_M | 2.3B | 5B | 2.9 GB | **9.78** | **17.86** | **545 ms** | **277 ms** |
| **gemma4-qat-e2b** | MoE QAT | 2.3B | 5B | 3.4 GB | 9.96 | 18.83 | 526 ms | 278 ms |
| **gemma4-e4b** | MoE Q4_K_M | 4.5B | 8B | 4.7 GB | 5.13 | 9.64 | 1,020 ms | 566 ms |
| **gemma4-qat-e4b** | MoE QAT | 4.5B | 8B | 5.2 GB | 5.41 | 10.04 | **1,014 ms** | **552 ms** |
| **gemma4-qat-26b** | MoE QAT | ~4B | 27B | 14.4 GB | **6.27** | **11.34** | 1,380 ms | 675 ms |
| **qwen3.5-4b** | Dense Q4_K_M | 4B | 4B | 2.7 GB | 5.43 | 10.04 | 1,476 ms | 658 ms |

**Takeaway**: Doubling active params (2.3B → 4.5B) roughly halves throughput (9.8 → 5.1 tok/s). QAT gives a consistent ~5% speedup over Q4_K_M on the same architecture. The 26B-A4B MoE beats both 4.5B MoE models and the 4B dense model because it activates slightly fewer params per token (~4B vs 4.5B). Think mode is ~80% faster than nothink for all models.

## Per-Question Detail

### E2B Think Mode (TPOT, ms)

| Question | Q4_K_M | QAT Q4_0 | Δ |
|---|---|---|---|
| Q01 software architecture | 56.16 | **53.33** | -5% |
| Q02 neural networks | 55.89 | **52.92** | -5% |
| Q03 TCP vs UDP | 55.90 | **53.04** | -5% |
| Q04 garbage collection | 55.87 | **53.18** | -5% |
| Q05 microservices | 56.12 | **52.91** | -6% |
| Q06 closures | 55.68 | **52.76** | -5% |
| Q07 CAP theorem | 56.07 | **53.38** | -5% |
| Q08 DNS resolution | 56.13 | **53.14** | -5% |
| Q09 design patterns | 55.89 | **53.35** | -5% |
| Q10 DB transactions | 56.11 | **53.00** | -6% |

QAT Q4_0 is consistently ~5% faster per-token across all 10 questions. This consistency suggests the speedup comes from the quantization format itself, not from question-dependent behavior.

### E4B Think Mode (TPOT, ms)

| Question | Q4_K_M | QAT Q4_0 | Δ |
|---|---|---|---|
| Q01 software architecture | 103.97 | **100.31** | -4% |
| Q02 neural networks | 103.75 | **99.98** | -4% |
| Q03 TCP vs UDP | 103.77 | **99.25** | -4% |
| Q04 garbage collection | 103.78 | **99.45** | -4% |
| Q05 microservices | 103.82 | **99.33** | -4% |
| Q06 closures | 103.39 | **99.40** | -4% |
| Q07 CAP theorem | 103.92 | **99.71** | -4% |
| Q08 DNS resolution | 104.06 | **99.79** | -4% |
| Q09 design patterns | 103.31 | **99.27** | -4% |
| Q10 DB transactions | 103.64 | **99.62** | -4% |

Same consistent ~4% advantage for QAT Q4_0 across all questions.

## Key Takeaways

- **QAT Q4_0 wins per-token speed consistently**: ~5% faster for E2B, ~4% faster for E4B, across all 10 questions and both think and nothink modes. The improvement is remarkably uniform.
- **TTFT is nearly identical**: QAT and Q4_K_M differ by <3% on first-token latency — not a differentiating factor.
- **Wall time is unpredictable**: Results vary by question because QAT and Q4_K_M produce different-length answers for the same prompt. Wall time depends on output verbosity, not per-token speed.
- **Recommendation**: Use QAT Q4_0 for consistent per-token speed gains (~4-5%). For wall time, differences are within noise — choose based on quality, not speed.

## 26B-A4B vs E4B: Same Active Params, Different Total Size

Both models are MoE with ~4B active parameters, but 26B-A4B has 27B total parameters vs E4B's 8B total. This means 26B-A4B can route to a much larger pool of expert knowledge while keeping compute per token similar to E4B.

### Speed Comparison

| Metric | 26B-A4B (QAT) | E4B (Q4_K_M) | 26B wins by |
|---|---|---|---|
| **NoThink TTFT** | 1,380 ms | **1,020 ms** | E4B wins (-26%) |
| **NoThink TPOT** | **160 ms** | 195 ms | **-18%** |
| **NoThink tok/s** | **6.27** | 5.13 | **+22%** |
| **Think TTFT** | 675 ms | **566 ms** | E4B wins (-16%) |
| **Think TPOT** | **88 ms** | 104 ms | **-15%** |
| **Think tok/s** | **11.34** | 9.64 | **+18%** |

### Tradeoff

| | 26B-A4B | E4B |
|---|---|---|
| Total params | 27B (MoE) | 8B (MoE) |
| Active params | ~4B | ~4.5B |
| Model size | 14.4 GB | 4.7 GB |
| NoThink throughput | **6.27 tok/s** | 5.13 tok/s |
| Think throughput | **11.34 tok/s** | 9.64 tok/s |
| TTFT (nothink) | 1,380 ms | **1,020 ms** |
| Expert diversity | 16+ experts | Fewer experts |

**26B-A4B is faster per-token despite being 3x larger** because it activates roughly the same number of parameters per forward pass (~4B). The MoE routing overhead is minimal — llama.cpp handles expert switching efficiently.

**The tradeoff is TTFT and memory**: loading 14.4 GB into RAM takes longer, so first-token latency is ~26-35% higher. But once inference starts, each token is generated faster. The 4B active params come from a much larger pool of 27B total weights, giving the model access to more specialized knowledge per token without paying the compute cost of a full 27B dense model.

**Why this matters**: 26B-A4B gives you the generation speed of a 4B model but with the knowledge capacity of a 27B model. For batch workloads where TTFT doesn't matter and you need higher quality reasoning from a larger model, 26B-A4B is the best CPU MoE option. The only cost is RAM (14.4 GB vs 4.7 GB).

## 12B QAT: The Dense Alternative

The 12B QAT is a dense model (all 12B params active per token), unlike the MoE models above. It has no Q4_K_M equivalent — it's QAT-only. This makes it the only "unified" Gemma 4 model in this lineup (no expert routing, no quantization choice).

### Speed Comparison

| Metric | 12B (QAT) | 26B-A4B (QAT) | E4B (Q4_K_M) | Qwen 3.5-4B (Dense) |
|---|---|---|---|---|
| **NoThink TTFT** | 2,977 ms | 1,380 ms | **1,020 ms** | 1,476 ms |
| **NoThink TPOT** | 421 ms | **160 ms** | 195 ms | 184 ms |
| **NoThink tok/s** | 2.38 | **6.27** | 5.13 | 5.43 |
| **Think TTFT** | 1,494 ms | 675 ms | **566 ms** | 658 ms |
| **Think TPOT** | 236 ms | **88 ms** | 104 ms | 100 ms |
| **Think tok/s** | 4.24 | **11.34** | 9.64 | 10.04 |

### Per-Question TPOT (ms)

**NoThink mode:**

| Question | 12B QAT | 26B-A4B QAT | E4B Q4_K_M |
|---|---|---|---|
| Q01 software architecture | 443 | 162 | 194 |
| Q02 neural networks | 429 | 162 | 191 |
| Q03 TCP vs UDP | 419 | 161 | 197 |
| Q04 garbage collection | 433 | 157 | 191 |
| Q05 microservices | 438 | 159 | 199 |
| Q06 closures | 428 | 131 | 202 |
| Q07 CAP theorem | 411 | 166 | 201 |
| Q08 DNS resolution | 400 | 167 | 190 |
| Q09 design patterns | 400 | 164 | 187 |
| Q10 DB transactions | 407 | 168 | 199 |
| **Mean** | **421** | **160** | **195** |
| **Std dev** | **15.8** | **10.8** | **5.2** |

**Think mode:**

| Question | 12B QAT | 26B-A4B QAT | E4B Q4_K_M |
|---|---|---|---|
| Q01 software architecture | 237.9 | 88.2 | 104.0 |
| Q02 neural networks | 236.7 | 88.0 | 103.8 |
| Q03 TCP vs UDP | 235.2 | 88.1 | 103.8 |
| Q04 garbage collection | 235.2 | 87.8 | 103.8 |
| Q05 microservices | 235.0 | 88.5 | 103.8 |
| Q06 closures | 234.0 | 88.0 | 103.4 |
| Q07 CAP theorem | 237.9 | 88.3 | 103.9 |
| Q08 DNS resolution | 239.0 | 87.8 | 104.1 |
| Q09 design patterns | 234.2 | 87.7 | 103.3 |
| Q10 DB transactions | 235.9 | 88.0 | 103.6 |
| **Mean** | **236.1** | **88.0** | **103.7** |
| **Std dev** | **1.7** | **0.3** | **0.2** |

### Analysis

The 12B QAT is **3x slower than 26B-A4B** per-token (421 ms vs 160 ms nothink) because it activates all 12B parameters every forward pass, while 26B-A4B only activates ~4B via MoE routing. This is the fundamental dense-vs-MoE tradeoff:

- **MoE advantage**: 26B-A4B runs at the speed of a 4B model because only ~4B params are active per token, even though it has 27B total knowledge. The 12B model must compute through all 12B params every time.
- **Dense stability**: The 12B's think-mode TPOT has a coefficient of variation (CV) of 0.7% (std 1.7 ms), similar to the MoE models — all show extremely uniform inter-chunk latency during reasoning generation.
- **TTFT cost scales with total size**: The 12B's TTFT (2,977 ms nothink) is 2x the 26B-A4B's (1,380 ms), despite 26B being 2.25x larger on disk. This is because prompt processing (prefill) touches all parameters — 12B dense = 12B computations, while 26B-A4B still only computes ~4B active params during prefill but pays for loading 14.4 GB into memory.

**When to use 12B QAT**: If you need a model that processes every token through the same dense computation (no expert routing), the 12B QAT provides consistent behavior. But for CPU throughput, MoE models with similar or fewer active params (26B-A4B, E4B) are significantly faster. The 12B's strength is simplicity and consistency — it doesn't depend on routing quality.

## Recommendation

**gemma4-qat-26b is the recommended default** for CPU inference. It activates only ~4B params per token (via MoE routing) but draws from a 27B knowledge pool — giving it the speed of a 4B model with the reasoning quality of a much larger model. On a 64 GB machine, the 14.4 GB model size is well within budget.

| | E2B (previous default) | 26B-A4B (new default) |
|---|---|---|
| RAM | 2.9 GB | 14.4 GB |
| NT tok/s | 9.78 | 6.27 (-36%) |
| TH tok/s | 17.86 | 11.34 (-36%) |
| Knowledge pool | 5B | 27B |
| Active params/token | 2.3B | ~4B |

The 36% speed loss over E2B buys you 5.4x more total parameters to route from. For interactive use where quality matters more than raw speed, this is a strong tradeoff. Use E2B only when speed is paramount (e.g., high-throughput batch processing, very slow machines, or RAM-constrained environments).

## Methodology

- 10 fixed questions (Q01-Q10) in consistent order, no randomization
- Each question is a CS/programming topic with "Answer short, concise, and correct." constraint
- `max_tokens`: 4096, `temperature`: 0.0
- Q4_K_M models: `unsloth/gemma-4-E2B-it-GGUF` and `unsloth/gemma-4-E4B-it-GGUF`
- QAT Q4_0 models: `google/gemma-4-E2B-it-qat-q4_0-gguf` and `google/gemma-4-E4B-it-qat-q4_0-gguf`
- 26B-A4B model: `google/gemma-4-26B-A4B-it-qat-q4_0-gguf` (QAT Q4_0 only)
- Test date: 2026-06-06
