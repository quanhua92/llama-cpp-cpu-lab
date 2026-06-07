# Qwen 3.6 35B-A3B vs Gemma 4 26B-A4B — CPU Benchmark Comparison

**Date:** 2026-06-07
**Machine:** Intel i7-10700 (8C/16T, 2.9–4.8 GHz) · 64 GB RAM · CPU-only (`-ngl 0`, `-t 8`, `-c 8192`)

## Models

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Architecture** | MoE (Mixture of Experts) | MoE (Gated DeltaNet + Gated Attention + MoE) |
| **Total params** | 26B | 35B |
| **Active params** | ~4B | ~3B |
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
| **TTFT** | 1380 ms | 727 ms | Qwen **47% faster** |
| **TPOT** | 160 ms | 96 ms | Qwen **40% faster** |
| **Throughput** | 6.27 tok/s | 10.45 tok/s | Qwen **67% faster** |
| **Avg wall time** | 32.3s | 9.0s | Qwen **72% faster** |

**Qwen 3.6 dominates no-think mode.** 67% higher throughput despite 8B more total parameters. This is because Qwen activates only ~3B params per token (vs ~4B for Gemma), and the smaller active parameter set dominates CPU inference cost. Additionally, Gemma 4's no-think mode still generates verbose markdown-formatted answers, while Qwen's answers are more concise.

### Think Mode (reasoning on)

| Metric | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B | Delta |
|---|---|---|---|
| **TTFT** | 675 ms | 706 ms | Gemma **4% faster** |
| **TPOT** | 88 ms | 99 ms | Gemma **12% faster** |
| **Throughput** | 11.34 tok/s | 10.08 tok/s | Gemma **12% faster** |
| **Avg wall time** | 62.6s | 57.6s | Qwen **8% faster** |

**Think mode is much closer.** Gemma has a 12% per-token advantage, but Qwen produces shorter thinking blocks and shorter answers, resulting in 8% lower wall time overall.

**Why the think/nothink flip?** In think mode, TPOT includes reasoning tokens (both models generate thinking chunks at the same speed they generate output). Gemma's thinking is free-form brainstorming — lots of short bullet points. Qwen's thinking is structured step-by-step with longer reasoning chains. The net effect: Gemma generates more total chunks per question, but each chunk is faster to produce.

**TTFT is 2x faster in think mode for Gemma** (675ms vs 1380ms), but barely changes for Qwen (706ms vs 727ms). This is because thinking mode pre-fills the thinking prefix, which the KV cache handles efficiently. In no-think mode, the full prompt must be re-processed each time.

### Per-Question Breakdown (No-Think)

| Q | Gemma TTFT | Qwen TTFT | Gemma TPOT | Qwen TPOT |
|---|---|---|---|---|
| Q01 Architecture | 1541ms | 680ms | 162ms | 97ms |
| Q02 Neural nets | 1425ms | 743ms | 162ms | 99ms |
| Q03 TCP/UDP | 1529ms | 837ms | 161ms | 95ms |
| Q04 Python GC | 1335ms | 763ms | 157ms | 96ms |
| Q05 Microservices | 1354ms | 665ms | 159ms | 96ms |
| Q06 Closure | 1201ms | 752ms | 131ms | 91ms |
| Q07 CAP theorem | 1289ms | 703ms | 166ms | 97ms |
| Q08 DNS | 1451ms | 712ms | 167ms | 97ms |
| Q09 Design patterns | 1305ms | 719ms | 164ms | 92ms |
| Q10 Transactions | 1372ms | 701ms | 168ms | 97ms |

Gemma's TTFT ranges 1201-1541ms. Qwen's ranges 665-837ms. The gap is consistent across all questions. TPOT follows the same pattern: Gemma 131-168ms vs Qwen 91-99ms.

### Per-Question Breakdown (Think)

| Q | Gemma TTFT | Qwen TTFT | Gemma TPOT | Qwen TPOT | Gemma Chunks | Qwen Chunks |
|---|---|---|---|---|---|---|
| Q01 Architecture | 688ms | 616ms | 89ms | 99ms | 823 | 476 |
| Q02 Neural nets | 676ms | 717ms | 88ms | 99ms | 633 | 579 |
| Q03 TCP/UDP | 701ms | 794ms | 89ms | 99ms | 849 | 471 |
| Q04 Python GC | 676ms | 719ms | 90ms | 99ms | 956 | 614 |
| Q05 Microservices | 654ms | 658ms | 87ms | 99ms | 496 | 446 |
| Q06 Closure | 728ms | 750ms | 86ms | 100ms | 322 | 948 |
| Q07 CAP theorem | 660ms | 718ms | 90ms | 100ms | 885 | 673 |
| Q08 DNS | 667ms | 701ms | 90ms | 99ms | 904 | 726 |
| Q09 Design patterns | 681ms | 721ms | 88ms | 99ms | 609 | 362 |
| Q10 Transactions | 620ms | 662ms | 87ms | 99ms | 526 | 447 |

Notable: Q06 (closure) — Qwen generated 948 chunks (95s) vs Gemma's 322 (28s) for the same one-sentence answer. Qwen's thinking was absurdly verbose: 260 lines of meta-commentary ("Final check", "Proceeds", "Done") before outputting a 20-word answer. This is Qwen's main weakness in think mode — it over-thinks simple questions.

### Speed Winner: Qwen 3.6

Qwen wins no-think mode decisively (67% higher throughput). Think mode is closer but Qwen still wins on wall time due to shorter outputs. Gemma wins per-token speed in think mode but loses on total time.

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
| **TTFT** | 928ms | 877ms |
| **Throughput** | 10.6 tok/s | 10.0 tok/s |
| **Tokens** | 1775 | 1020 |
| **Total time** | 169s | 103s |

**Gemma:** Opens with a detailed outline (sender, recipient, tone, themes, structure plan — 40 lines of thinking). Writes a literary letter from a Saigon cafe, asking about climate change, AI, culture. Uses evocative language ("bầu trời trong vắt", "sợi dây vô hình"). Ends with a signature "Một người bạn từ năm 2026." The letter is ~650 words, literary tone, well-structured.

**Qwen:** Shorter thinking (4 paragraphs of planning). Writes from Đà Nẵng, not Saigon. Covers climate adaptation (smart dikes, rooftop gardens), AI in healthcare/education, preserving traditions (Phở, coffee culture). Ends with a sign-off and location/date. ~450 words, warm but slightly more didactic.

**Verdict: Tie.** Gemma's letter is more literary and atmospheric. Qwen's is more practical and grounded. Both are excellent Vietnamese. Gemma writes longer (1775 vs 1020 tokens), which isn't necessarily better for a "letter" format.

### Reflect Example: Professional Chef Introduces Pho

Both models hit max_tokens in step 1 (initial generation cuts off mid-sentence). The 3-step reflect flow catches this:

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B |
|---|---|---|
| **Total time** | 429s | 437s |
| **Total tokens** | 3666 | 4096 |
| **Throughput** | 9.9 tok/s | 9.9 tok/s |

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
| **Token efficiency** | Cuts off at 1775/4096 | Cuts off at ~500/2048 (step 1) |

Both models handle Vietnamese creative writing well. The reflect flow produces high-quality results for both. The main difference is style preference: Gemma is more literary, Qwen is more practical.

---

## Overall Verdict

| | Gemma 4 26B-A4B | Qwen 3.6 35B-A3B | Winner |
|---|---|---|---|
| **No-think speed** | 6.27 tok/s | 10.45 tok/s | **Qwen (+67%)** |
| **Think speed (TPOT)** | 88 ms | 99 ms | **Gemma (+12%)** |
| **Think wall time** | 62.6s | 57.6s | **Qwen (-8%)** |
| **Factual response quality** | Verbose, ignores constraints | Concise, follows constraints | **Qwen** |
| **Creative writing quality** | Literary, atmospheric | Practical, grounded | **Tie** |
| **Reflect (3-step) quality** | Works well, concise thinking | Works well, detailed thinking | **Tie** |
| **Thinking efficiency** | Concise brainstorming | Over-thinks simple questions | **Gemma** |
| **File size** | 14.4 GB | 22.1 GB | **Gemma (-35%)** |
| **Vision support** | Yes (GGUF: text-only) | Yes (GGUF: text-only) | **Tie** |

**Qwen 3.6 35B-A3B is the better model for CPU-only use cases.** It's significantly faster in no-think mode, competitive in think mode, and produces higher-quality factual responses that respect user constraints. Creative writing quality is equivalent. The main caveat: Qwen over-thinks trivially simple questions in think mode (e.g., 260 lines of thinking for a one-sentence closure answer), wasting tokens.

**However, for GPU deployment with 16 GB VRAM, Gemma 4 26B-A4B is the better default.** At 14 GB it fits entirely in VRAM (`-ngl 99`), while Qwen 3.6 35B-A3B at 21 GB would need to offload layers to system RAM, negating much of the GPU speed advantage. Size matters when VRAM is the constraint.
