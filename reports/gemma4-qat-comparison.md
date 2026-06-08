# Gemma 4 Q4_K_M vs QAT Q4_0 Comparison

> CPU: Intel i7-10700 (8C/16T, 2.9-4.8 GHz) | RAM: 64 GB | llama.cpp commit `4da6370`
> Q4_K_M = post-training quantization | QAT Q4_0 = quantization-aware training
> Bold = faster value in each category. Averages over 10 fixed questions.

## TTFT (ms) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | **241** | 251 | 292 | **283** |
| E4B | **468** | 480 | 570 | **565** |

## Decode Speed (tok/s) — higher is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | 18.16 | **19.20** | 17.87 | **18.91** |
| E4B | 9.71 | **10.25** | 9.55 | **10.10** |

## Prompt Speed (tok/s) — higher is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | **96.2** | 93.2 | **87.9** | 89.5 |
| E4B | **49.0** | 48.2 | **45.0** | 45.6 |

## Wall Duration (s) — lower is better

| Model | Q4_K_M NoThink | QAT Q4_0 NoThink | Q4_K_M Think | QAT Q4_0 Think |
|---|---|---|---|---|
| E2B | **6.1** | 7.2 | 23.9 | **22.7** |
| E4B | 13.2 | **11.6** | 58.8 | **54.3** |

## All MoE Models at a Glance

Decode speed scales with **active params**, not total model size. This is why 26B-A4B (25.2B total, ~3.8B active) is faster per-token than E4B (4.5B total, 4.5B active).

| Model | Type | Active | Total | Size | NT dec (tok/s) | TH dec (tok/s) | NT TTFT | TH TTFT |
|---|---|---|---|---|---|---|---|---|
| **gemma4-e2b** | Dense Q4_K_M | 2.3B | 2.3B | 2.9 GB | 18.16 | 17.87 | **241 ms** | 292 ms |
| **gemma4-qat-e2b** | Dense QAT | 2.3B | 2.3B | 3.4 GB | **19.20** | **18.91** | 251 ms | **283 ms** |
| **gemma4-e4b** | Dense Q4_K_M | 4.5B | 4.5B | 4.7 GB | 9.71 | 9.55 | **468 ms** | 570 ms |
| **gemma4-qat-e4b** | Dense QAT | 4.5B | 4.5B | 5.2 GB | **10.25** | **10.10** | 480 ms | **565 ms** |
| **gemma4-qat-26b-a4b** | MoE QAT | ~3.8B | 25.2B | 14.4 GB | **11.90** | **11.36** | 616 ms | 671 ms |
| **qwen3.5-4b** | Dense Q4_K_M | 4B | 4B | 2.7 GB | 10.29 | 9.87 | 678 ms | 640 ms |

**Takeaway**: Decode speed scales with model size for dense models — doubling params roughly halves tok/s (2.3B → 4.5B: 18.2 → 9.7). QAT gives ~6% speedup over Q4_K_M on the same architecture. The 26B-A4B is the only MoE model — it activates ~3.8B params per token from a 25.2B pool, beating the 4.5B dense models in speed while having much more knowledge.

## Per-Question Detail

### E2B Think Mode (Decode tok/s)

| Question | Q4_K_M | QAT Q4_0 | Δ |
|---|---|---|---|
| Q01 software architecture | 17.85 | **18.90** | +6% |
| Q02 neural networks | 17.92 | **19.04** | +6% |
| Q03 TCP vs UDP | 17.90 | **18.88** | +6% |
| Q04 garbage collection | 17.90 | **19.01** | +6% |
| Q05 microservices | 17.89 | **18.99** | +6% |
| Q06 closures | 17.94 | **19.02** | +6% |
| Q07 CAP theorem | 17.82 | **18.79** | +5% |
| Q08 DNS resolution | 17.75 | **18.72** | +5% |
| Q09 design patterns | 17.86 | **19.00** | +6% |
| Q10 DB transactions | 17.89 | **18.95** | +6% |

QAT Q4_0 is consistently ~6% faster per-token across all 10 questions. This consistency suggests the speedup comes from the quantization format itself, not from question-dependent behavior.

### E4B Think Mode (Decode tok/s)

| Question | Q4_K_M | QAT Q4_0 | Δ |
|---|---|---|---|
| Q01 software architecture | 9.52 | **10.06** | +6% |
| Q02 neural networks | 9.57 | **10.06** | +5% |
| Q03 TCP vs UDP | 9.55 | **10.14** | +6% |
| Q04 garbage collection | 9.57 | **10.14** | +6% |
| Q05 microservices | 9.57 | **10.16** | +6% |
| Q06 closures | 9.63 | **10.17** | +6% |
| Q07 CAP theorem | 9.51 | **10.08** | +6% |
| Q08 DNS resolution | 9.49 | **10.08** | +6% |
| Q09 design patterns | 9.64 | **10.17** | +5% |
| Q10 DB transactions | 9.55 | **10.08** | +6% |

Same consistent ~6% advantage for QAT Q4_0 across all questions.

## Key Takeaways

- **QAT Q4_0 wins decode speed consistently**: ~6% faster for E2B, ~6% faster for E4B, across all 10 questions and both think and nothink modes. The improvement is remarkably uniform.
- **TTFT is nearly identical**: QAT and Q4_K_M differ by <5% on first-token latency — not a differentiating factor.
- **Wall time is unpredictable**: Results vary by question because QAT and Q4_K_M produce different-length answers for the same prompt. Wall time depends on output verbosity, not per-token speed.
- **Recommendation**: Use QAT Q4_0 for consistent per-token speed gains (~6%). For wall time, differences are within noise — choose based on quality, not speed.

## 26B-A4B vs E4B: Same Active Params, Different Total Size

Both models have ~3.8B active parameters per token, but 26B-A4B is MoE (25.2B total parameters) while E4B is dense (4.5B total parameters). This means 26B-A4B can route to a much larger pool of expert knowledge while keeping compute per token similar to E4B.

### Speed Comparison

| Metric | 26B-A4B (QAT) | E4B (Q4_K_M) | Winner |
|---|---|---|---|
| **NoThink TTFT** | 616 ms | **468 ms** | E4B (-24%) |
| **NoThink Decode** | **11.90 tok/s** | 9.71 tok/s | **26B (+23%)** |
| **Think TTFT** | 671 ms | **570 ms** | E4B (-15%) |
| **Think Decode** | **11.36 tok/s** | 9.55 tok/s | **26B (+19%)** |

### Tradeoff

| | 26B-A4B | E4B |
|---|---|---|
| Total params | 26B (MoE) | 4.5B (Dense) |
| Active params | ~3.8B | ~4.5B |
| Model size | 14.4 GB | 4.7 GB |
| NoThink decode | **11.90 tok/s** | 9.71 tok/s |
| Think decode | **11.36 tok/s** | 9.55 tok/s |
| TTFT (nothink) | 616 ms | **468 ms** |
| Expert diversity | 128 total (8 routed + 1 shared) | None (dense) |

**26B-A4B is faster per-token despite being 6x larger** because it activates roughly the same number of parameters per forward pass (~3.8B) as the 4.5B dense E4B model. The MoE routing overhead is minimal — llama.cpp handles expert switching efficiently.

**The tradeoff is TTFT and memory**: loading 14.4 GB into RAM takes longer, so first-token latency is ~24-32% higher. But once inference starts, each token is generated faster. The ~3.8B active params come from a much larger pool of 26B total weights, giving the model access to more specialized knowledge per token without paying the compute cost of a full 31B dense model.

**Why this matters**: 26B-A4B gives you the generation speed of a ~4B model but with the knowledge capacity of a 26B model. For batch workloads where TTFT doesn't matter and you need higher quality reasoning from a larger model, 26B-A4B is the best CPU MoE option. The only cost is RAM (14.4 GB vs 4.7 GB).

## 12B QAT: The Dense Alternative

The 12B QAT is a dense model (all 12B params active per token), unlike the MoE models above. Google only provides QAT Q4_0 quantization officially — community Q4_K_M GGUFs are available from Unsloth. This makes our 12B data QAT-only. The "Unified" in 12B means it's encoder-free: image/audio projections go directly into the LLM embedding space, unlike other Gemma 4 models which use dedicated encoders.

### Speed Comparison

| Metric | 12B (QAT) | 26B-A4B (QAT) | E4B (Q4_K_M) | Qwen 3.5-4B (Dense) |
|---|---|---|---|---|
| **NoThink TTFT** | 1,494 ms | 616 ms | **468 ms** | 678 ms |
| **NoThink Decode** | 4.35 tok/s | **11.90 tok/s** | 9.71 tok/s | 10.29 tok/s |
| **Think TTFT** | 1,532 ms | 671 ms | **570 ms** | 640 ms |
| **Think Decode** | 4.23 tok/s | **11.36 tok/s** | 9.55 tok/s | 9.87 tok/s |

### Per-Question Decode Speed (tok/s)

**NoThink mode:**

| Question | 12B QAT | 26B-A4B QAT | E4B Q4_K_M |
|---|---|---|---|
| Q01 software architecture | 4.35 | **11.79** | 9.61 |
| Q02 neural networks | 4.36 | **11.94** | 9.73 |
| Q03 TCP vs UDP | 4.36 | **11.92** | 9.74 |
| Q04 garbage collection | 4.36 | **11.96** | 9.75 |
| Q05 microservices | 4.37 | **12.01** | 9.69 |
| Q06 closures | 4.42 | **12.03** | 9.79 |
| Q07 CAP theorem | 4.34 | **11.83** | 9.74 |
| Q08 DNS resolution | 4.33 | **11.90** | 9.68 |
| Q09 design patterns | 4.38 | **11.93** | 9.91 |
| Q10 DB transactions | 4.34 | **11.98** | 9.68 |

**Think mode:**

| Question | 12B QAT | 26B-A4B QAT | E4B Q4_K_M |
|---|---|---|---|
| Q01 software architecture | 4.21 | **11.32** | 9.52 |
| Q02 neural networks | 4.23 | **11.50** | 9.57 |
| Q03 TCP vs UDP | 4.26 | **11.28** | 9.55 |
| Q04 garbage collection | 4.26 | **11.19** | 9.57 |
| Q05 microservices | 4.28 | **11.59** | 9.57 |
| Q06 closures | 4.29 | **11.75** | 9.63 |
| Q07 CAP theorem | 4.20 | **11.23** | 9.51 |
| Q08 DNS resolution | 4.18 | **11.24** | 9.49 |
| Q09 design patterns | 4.30 | **11.47** | 9.64 |
| Q10 DB transactions | 4.25 | **11.54** | 9.55 |

### Analysis

The 12B QAT is **3x slower than 26B-A4B** per-token (4.35 vs 11.90 tok/s nothink) because it activates all 12B parameters every forward pass, while 26B-A4B only activates ~3.8B via MoE routing. This is the fundamental dense-vs-MoE tradeoff:

- **MoE advantage**: 26B-A4B runs at the speed of a ~4B model because only ~3.8B params are active per token, even though it has 26B total knowledge. The 12B model must compute through all 12B params every time.
- **Dense stability**: The 12B's think-mode decode speed has extremely low variance — all 10 questions produce 4.18–4.30 tok/s. The MoE models show similar stability (26B-A4B: 11.19–11.75 tok/s).
- **TTFT cost scales with total size**: The 12B's TTFT (1,494 ms nothink) is 2.4x the 26B-A4B's (616 ms), despite 26B being 2.25x larger on disk. This is because prompt processing (prefill) touches all parameters — 12B dense = 12B computations, while 26B-A4B still only computes ~3.8B active params during prefill but pays for loading 14.4 GB into memory.

**When to use 12B QAT**: If you need a model that processes every token through the same dense computation (no expert routing), the 12B QAT provides consistent behavior. But for CPU throughput, the MoE 26B-A4B (with ~3.8B active params) and dense models with similar size are significantly faster. The 12B's strength is simplicity and consistency — it doesn't depend on routing quality.

## Recommendation

**gemma4-qat-26b-a4b is the recommended default** for CPU inference. It activates only ~3.8B params per token (via MoE routing) but draws from a 25.2B knowledge pool — giving it the speed of a ~4B model with the reasoning quality of a much larger model. On a 64 GB machine, the 14.4 GB model size is well within budget.

| | E2B (previous default) | 26B-A4B (new default) |
|---|---|---|
| RAM | 2.9 GB | 14.4 GB |
| NT tok/s | 18.16 | 11.90 (-34%) |
| TH tok/s | 17.87 | 11.36 (-36%) |
| Knowledge pool | 2.3B | 26B |
| Active params/token | 2.3B | ~3.8B |

The 34-36% speed loss over E2B buys you 11x more total parameters to route from. For interactive use where quality matters more than raw speed, this is a strong tradeoff. Use E2B only when speed is paramount (e.g., high-throughput batch processing, very slow machines, or RAM-constrained environments).

## Methodology

- 10 fixed questions (Q01-Q10) in consistent order, no randomization
- Each question is a CS/programming topic with "Answer short, concise, and correct." constraint
- `max_tokens`: 4096, `temperature`: 0.0
- Q4_K_M models: `unsloth/gemma-4-E2B-it-GGUF` and `unsloth/gemma-4-E4B-it-GGUF`
- QAT Q4_0 models: `google/gemma-4-E2B-it-qat-q4_0-gguf` and `google/gemma-4-E4B-it-qat-q4_0-gguf`
- 26B-A4B model: `google/gemma-4-26B-A4B-it-qat-q4_0-gguf` (QAT Q4_0 only)
- All metrics: server-side `predicted_per_second` (decode speed) and `prompt_per_second` (prompt speed)
- All models: 10 questions completed, 0 failures
