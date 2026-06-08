# Qwen 3.6 35B-A3B vs Gemma 4 26B-A4B — CPU Benchmark Comparison

**Date:** 2026-06-08
**Machine:** Intel i7-10700 (8C/16T, 2.9–4.8 GHz) · 64 GB RAM · CPU-only (`-ngl 0`, `-t 8`, `-c 8192`)

## Models

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Architecture** | MoE (Mixture of Experts) | MoE (Gated DeltaNet + Gated Attention + MoE) |
| **Total params** | 26B | 35B |
| **Active params** | ~3.8B | ~3B |
| **Experts** | 128 total (8 routed + 1 shared) | 256 total (8 routed + 1 shared) |
| **Quantization** | Q4_0 (QAT) | UD-Q4_K_M (Unsloth Dynamic) |
| **File size** | 14.4 GB | 22.1 GB |
| **Context length** | 256K | 262K |
| **Vision** | Yes (text-only in our GGUF/llama.cpp) | Yes (vision-language, text-only in our GGUF/llama.cpp) |
| **Default thinking** | Yes | Yes |
| **Arch tag** | gemma4 | qwen35moe |

---

## 1. Speed Comparison

### No-Think Mode (reasoning off)

| Metric | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B | Delta |
|---|---|---|---|
| **TTFT** | **616 ms** | 748 ms | Gemma **18% faster** |
| **Decode speed** | **11.90 tok/s** | 10.37 tok/s | Gemma **15% faster** |
| **Avg wall time** | 16.5s | **8.9s** | Qwen **46% faster** |

**Gemma wins per-token speed in no-think mode.** 15% higher decode speed despite 8B fewer total parameters. Qwen activates only ~3B params per token (vs ~3.8B for Gemma), so the speed advantage goes to Gemma here — likely due to quantization format differences (Q4_0 QAT vs UD-Q4_K_M). However, Qwen wins wall time by 46% because it produces significantly shorter answers.

### Think Mode (reasoning on)

| Metric | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B | Delta |
|---|---|---|---|
| **TTFT** | **671 ms** | 723 ms | Gemma **7% faster** |
| **Decode speed** | **11.36 tok/s** | 10.24 tok/s | Gemma **11% faster** |
| **Avg wall time** | 62.5s | **56.8s** | Qwen **9% faster** |

**Gemma wins per-token in think mode too.** 11% decode advantage. But Qwen still wins wall time (9% faster) because it produces shorter thinking blocks and shorter final answers. Gemma's thinking is free-form brainstorming with many short bullet points, while Qwen's is structured step-by-step.

**TTFT is nearly unchanged in think mode for Gemma** (671ms vs 616ms) and barely changes for Qwen (723ms vs 748ms). This is because thinking mode pre-fills the thinking prefix, which the KV cache handles efficiently.

### Per-Question Breakdown (No-Think)

| Q | Gemma TTFT | Qwen TTFT | Gemma dec | Qwen dec |
|---|---|---|---|---|
| Q01 Architecture | 608ms | 693ms | 11.79 | 10.40 |
| Q02 Neural nets | 619ms | 781ms | 11.94 | 10.23 |
| Q03 TCP/UDP | 649ms | 816ms | 11.92 | 10.36 |
| Q04 Python GC | 656ms | 742ms | 11.96 | 10.39 |
| Q05 Microservices | 581ms | 708ms | 12.01 | 10.46 |
| Q06 Closure | 684ms | 822ms | 12.03 | 10.76 |
| Q07 CAP theorem | 581ms | 755ms | 11.83 | 10.32 |
| Q08 DNS | 612ms | 691ms | 11.90 | 10.37 |
| Q09 Design patterns | 609ms | 763ms | 11.93 | 10.50 |
| Q10 Transactions | 557ms | 705ms | 11.98 | 10.41 |

Gemma's TTFT ranges 557-684ms. Qwen's ranges 691-822ms. The gap is consistent across all questions. Decode speed follows the same pattern: Gemma 11.79-12.03 tok/s vs Qwen 10.23-10.76 tok/s.

### Per-Question Breakdown (Think)

| Q | Gemma TTFT | Qwen TTFT | Gemma dec | Qwen dec | Gemma Tokens | Qwen Tokens |
|---|---|---|---|---|---|---|
| Q01 Architecture | 688ms | 633ms | 11.32 | 10.07 | 825 | 476 |
| Q02 Neural nets | 670ms | 768ms | 11.50 | 10.27 | 635 | 579 |
| Q03 TCP/UDP | 727ms | 795ms | 11.28 | 10.29 | 851 | 471 |
| Q04 Python GC | 759ms | 714ms | 11.19 | 10.25 | 958 | 614 |
| Q05 Microservices | 644ms | 664ms | 11.59 | 10.28 | 498 | 446 |
| Q06 Closure | 628ms | 765ms | 11.75 | 10.22 | 324 | 948 |
| Q07 CAP theorem | 643ms | 722ms | 11.23 | 10.26 | 887 | 673 |
| Q08 DNS | 670ms | 720ms | 11.24 | 10.25 | 906 | 726 |
| Q09 Design patterns | 661ms | 770ms | 11.47 | 10.29 | 611 | 362 |
| Q10 Transactions | 620ms | 679ms | 11.54 | 10.28 | 528 | 447 |

Notable: Q06 (closure) — Qwen generated 948 tokens vs Gemma's 324 for the same one-sentence answer. Qwen's thinking was absurdly verbose: 260 lines of meta-commentary ("Final check", "Proceeds", "Done") before outputting a 20-word answer. This is Qwen's main weakness in think mode — it over-thinks simple questions.

### Speed Winner: Gemma (per-token), Qwen (wall time)

Gemma wins per-token decode speed in both modes (15% no-think, 11% think). Qwen wins wall time in both modes (46% no-think, 9% think) due to shorter outputs. The per-token gap is consistent across all questions.

---

## 2. Quality Comparison

All responses evaluated against the prompt constraint: "Answer short, concise, and correct."

### Q01: Software Architecture

**Gemma 26B-A4B:**
> **Software architecture** is the fundamental structure of a software system. It defines the high-level components, their relationships, and the principles guiding its design and evolution.
>
> ### Core Components
> * **Components:** The building blocks (modules, services, databases).
> * **Connectors:** The mechanisms allowing components to communicate...
> * ### Common Architectural Patterns
> * **Monolithic:** A single, unified unit...

**Qwen 3.6 35B-A3B:**
> Software architecture is the high-level structure of a software system, defining its components, their interactions, data flow, and the principles guiding design and evolution. It acts as a technical blueprint that ensures scalability, maintainability, security, and performance while aligning with business requirements. Common styles include monolithic, layered, microservices, event-driven, and serverless architectures. Effective architecture balances technical trade-offs to support long-term adaptability and system health.

**Verdict: Qwen.** Gemma writes a 150-word mini-article with markdown headers. Qwen gives a focused 55-word paragraph covering the same points. The prompt said "short, concise."

### Q02: Neural Networks

**Gemma:** 6-step explanation with bold headers. ~130 words.
**Qwen:** 4-step numbered list + closing. ~75 words.

**Verdict: Tie.** Both accurate. Qwen slightly more concise.

### Q03: TCP vs UDP

**Gemma:** Two sections with 5 bullet points each (reliability, connection, ordering, flow control, use cases). ~100 words.
**Qwen:** Two bullet points. ~40 words.

**Verdict: Qwen.** Covers all essential differences in half the words.

### Q04: Python Garbage Collection

**Gemma:** Two numbered sections with detailed explanations. ~120 words. Includes "Summary" section.
**Qwen:** Two numbered points + closing sentence. ~65 words.

**Verdict: Qwen.** Same information, half the length.

### Q05: Microservices

**Gemma:** Bold intro + 4 characteristic bullets + benefit + challenge. ~100 words.
**Qwen:** 3 sentences. ~45 words.

**Verdict: Qwen.** Gemma adds "Main Challenge" which wasn't asked. Qwen stays on topic.

### Q06: Closure

**Gemma:** 1 sentence + 1-sentence summary. ~30 words.
**Qwen:** 1 sentence. ~20 words.

**Verdict: Tie.** Both perfect for this simple question.

### Q07: CAP Theorem

**Gemma:** Numbered C/A/P list + "Core Rule" section with CP/AP/CA subsections. ~110 words.
**Qwen:** Bullet list + explanation. ~70 words.

**Verdict: Tie.** Both excellent. Gemma more structured, Qwen more compact.

### Q08: DNS Resolution

**Gemma:** 5-step numbered process. ~100 words. Includes local cache step.
**Qwen:** 5-step numbered process. ~55 words. Adds UDP port 53 detail.

**Verdict: Tie.** Gemma more complete (local cache), Qwen adds transport detail.

### Q09: Design Patterns

**Gemma:** 2 paragraphs + 3-category list. ~90 words.
**Qwen:** 2 sentences. ~35 words.

**Verdict: Qwen.** Respects "short, concise" constraint. Gemma over-delivers.

### Q10: Database Transactions

**Gemma:** Intro + 4 ACID bullets with detailed explanations. ~110 words.
**Qwen:** 2 sentences + inline ACID + commit/rollback. ~55 words.

**Verdict: Tie.** Both accurate. Qwen more compact.

### Quality Summary

| Aspect | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Instruction following** | Poor — ignores "short, concise" | Good — calibrated to constraints |
| **Technical accuracy** | Excellent | Excellent |
| **Completeness** | High — covers edge cases | Adequate — covers essentials |
| **Formatting** | Heavy markdown (headers, bullets, bold) | Clean, minimal formatting |
| **Verbosity** | 2-3x longer than necessary | Well-sized to prompt |
| **Thinking style** | Free-form brainstorming, concise | Structured (analyze→draft→check), sometimes over-thinks |

**Quality Winner: Qwen 3.6** — primarily due to superior instruction following. Both models are equally accurate, but Qwen respects the "short, concise" constraint consistently while Gemma ignores it and produces mini-articles for every answer.

---

## 3. Creative Writing Quality (Vietnamese Examples)

The benchmark prompts are short and factual. To test deeper quality, we compare the Vietnamese creative writing examples (ask: "letter to the future"; reflect: "professional chef introduces Pho").

### Ask Example: Letter to the Future (100 years, Vietnam 2026)

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Throughput** | 10.6 tok/s | 10.2 tok/s |
| **Tokens** | 1775 | 1020 |
| **Total time** | 168s | 101s |

**Gemma:** Opens with a detailed outline (sender, recipient, tone, themes, structure plan — 40 lines of thinking). Writes a literary letter from a Saigon cafe, asking about climate change, AI, culture. Uses evocative language ("bầu trời trong vắt", "sợi dây vô hình"). Ends with a signature "Một người bạn từ năm 2026." The letter is ~650 words, literary tone, well-structured.

**Qwen:** Shorter thinking (4 paragraphs of planning). Writes from Đà Nẵng, not Saigon. Covers climate adaptation (smart dikes, rooftop gardens), AI in healthcare/education, preserving traditions (Phở, coffee culture). Ends with a sign-off and location/date. ~450 words, warm but slightly more didactic.

**Verdict: Tie.** Gemma's letter is more literary and atmospheric. Qwen's is more practical and grounded. Both are excellent Vietnamese. Gemma writes longer (1775 vs 1020 tokens), which isn't necessarily better for a "letter" format.

### Reflect Example: Professional Chef Introduces Pho

Both models hit max_tokens in step 1 (initial generation cuts off mid-sentence). The 3-step reflect flow catches this:

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Total time** | 425s | 435s |
| **Total tokens** | 3666 | 4096 |
| **Throughput** | 10.0 tok/s | 10.0 tok/s |

**Step 1 (Initial Generation):**
- **Gemma:** Cuts off after listing spices in the broth section. Structured with emojis and English translations in parentheses. Professional chef persona.
- **Qwen:** Cuts off mid-sentence describing the broth clarity. Also uses emojis. Same chef persona.

**Step 2 (Self-Critique):**
- **Gemma:** Identifies the cutoff as a "Major Failure." Notes missing noodles, meat, herbs, condiments, how-to guide. Rates completeness "Very Low." Actionable feedback: finish the thought, add toppings, add "how to eat," mention regionality.
- **Qwen:** Also identifies cutoff. More detailed critique: analyzes clarity, completeness, accuracy, structure individually. Catches a minor inaccuracy (noodles are "ép qua khuôn" not "giã"). Proposes adding a "Cách thưởng thức" section.

**Step 3 (Revision):**
- **Gemma:** Produces a complete, polished response with 4 sections (Broth, Noodles, Protein, Herbs) + "Chef's Guide" section with 3 tips. Uses bilingual terms (English in parentheses). ~500 words. Well-structured, professional.
- **Qwen:** Produces a similar complete response with sections on Origin, Ingredients, How to Enjoy, and a closing invitation. Slightly shorter (~400 words). Corrects the noodle process. Adds emoji formatting.

**Verdict: Tie.** Both the 3-step reflect process works identically. Step 1 cuts off, step 2 catches it, step 3 delivers a polished result. The final outputs are comparable in quality. Gemma's thinking is more concise (free-form bullets). Qwen's thinking is verbose (structured analyze→draft→check, but sometimes meta-comments like "Proceeds" and "Done").

### Examples Summary

| Aspect | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Vietnamese fluency** | Excellent | Excellent |
| **Creative writing** | More literary, atmospheric | More practical, grounded |
| **Reflect flow (3-step)** | Works correctly | Works correctly |
| **Self-critique quality** | Concise, accurate | Detailed, accurate |
| **Final revision quality** | Polished, bilingual | Polished, emoji-rich |

Both models handle Vietnamese creative writing well. The reflect flow produces high-quality results for both. The main difference is style preference: Gemma is more literary, Qwen is more practical.

---

## Overall Verdict

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B | Winner |
|---|---|---|---|
| **No-think decode** | **11.90 tok/s** | 10.37 tok/s | **Gemma (+15%)** |
| **Think decode** | **11.36 tok/s** | 10.24 tok/s | **Gemma (+11%)** |
| **No-think wall time** | 16.5s | **8.9s** | **Qwen (-46%)** |
| **Think wall time** | 62.5s | **56.8s** | **Qwen (-9%)** |
| **No-think TTFT** | **616 ms** | 748 ms | **Gemma (-18%)** |
| **Think TTFT** | **671 ms** | 723 ms | **Gemma (-7%)** |
| **Factual response quality** | Verbose, ignores constraints | Concise, follows constraints | **Qwen** |
| **Creative writing quality** | Literary, atmospheric | Practical, grounded | **Tie** |
| **Reflect (3-step) quality** | Works well, concise thinking | Works well, detailed thinking | **Tie** |
| **Thinking efficiency** | Concise brainstorming | Over-thinks simple questions | **Gemma** |
| **File size** | **14.4 GB** | 22.1 GB | **Gemma (-35%)** |
| **Vision support** | Yes (GGUF: text-only) | Yes (GGUF: text-only) | **Tie** |

**Gemma 4 26B-A4B wins on raw throughput** — 15% faster decode in no-think, 11% in think, lower TTFT, and 35% smaller model file. It's the faster engine.

**Qwen 3.6 35B-A3B wins on output quality and efficiency** — it follows instructions better, produces appropriately concise responses, and wins wall time in both modes by generating fewer (but better-targeted) tokens. Its 3B active params vs Gemma's ~3.8B means it should theoretically be faster, but Q4_K_M quantization (vs QAT Q4_0) narrows or reverses that advantage.

**For CPU-only use, the choice depends on priority**: pick **Gemma** if raw speed and smaller file size matter (batch workloads, larger context windows). Pick **Qwen** if response quality and instruction following matter more (interactive use, constraint-aware generation).

**For GPU deployment with 16 GB VRAM, Gemma 4 26B-A4B is the better default.** At 14 GB it fits entirely in VRAM (`-ngl 99`), while Qwen 3.6 35B-A3B at 21 GB would need to offload layers to system RAM, negating much of the GPU speed advantage. Size matters when VRAM is the constraint.
