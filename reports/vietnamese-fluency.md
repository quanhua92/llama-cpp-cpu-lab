# Local LLM Vietnamese Fluency & Quality Report

**Date:** June 2026  
**Hardware:** Intel i9-13900K / Intel i7-10700 · 64 GB RAM · RTX 4060 Ti 16GB  
**Dataset:** 22 local LLMs tested using `llama.cpp` across two custom Vietnamese tasks:
1. **Ask Prompt (Creative Writing):** Write a letter to the future (100 years later, Year 2126) from the perspective of someone living in Vietnam in the year 2026.
2. **Reflect Prompt (Agentic Instruction):** Act as a professional chef introducing a signature Vietnamese dish to foreign tourists, using a 3-step self-reflection pipeline (Generate $\rightarrow$ Critique $\rightarrow$ Revise).

---

## 1. Executive Summary & Model Rankings

Linguistic capabilities in Vietnamese vary dramatically by model parameter size and training paradigm. Below is the ranking of all 22 tested models based on grammatical correctness, style preservation, temporal logic, and instruction-following.

| Rank | Model Key | Parameter Size | Architecture | Ask (Letter) Fluency | Reflect (Chef) Fluency | Overall Grade | Key Observation / Failure Mode |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `qwen3.6-35b-a3b` | 35B (MoE, ~3B) | MoE | Excellent | Excellent | **A+** | Rich vocabulary, flawless grammar, logical revision. |
| **2** | `gemma4-qat-26b-a4b` | 26B (MoE, ~3.8B) | MoE (QAT) | Excellent | Excellent | **A+** | Deeply evocative, literary Vietnamese; very natural. |
| **3** | `qwen3.6-27b` | 27B | Dense | Excellent | Excellent | **A** | Perfect syntax, slightly more formal than Gemma. |
| **4** | `gemma4-qat-31b` | 31B | Dense (QAT) | Excellent | Excellent | **A** | Highly descriptive; fits entirely in GPU VRAM (16GB). |
| **5** | `gemma4-qat-12b` | 12B | Dense (QAT) | Excellent | Excellent | **A-** | Encoder-free unified architecture; highly coherent. |
| **6** | `gemma4-qat-e4b` | 4.5B | Dense (QAT) | Excellent | Excellent | **B+** | Outperforms standard E4B in vocabulary diversity. |
| **7** | `gemma4-qat-e2b` | 2.3B | Dense (QAT) | Excellent | Excellent | **B+** | Evocative and poetic; best sub-3B model for Vietnamese. |
| **8** | `gemma4-e4b` | 4.5B | Dense | Excellent | Excellent | **B** | Great grammar, slightly less descriptive than QAT. |
| **9** | `gemma4-e2b` | 2.3B | Dense | Excellent | Excellent | **B** | Functional, coherent prose; slightly generic terms. |
| **10** | `qwen3.5-4b` | 4B | Dense | Good | Good | **B-** | Avoids the reasoning loops seen in smaller Qwen models. |
| **11** | `qwen2.5-3b` | 3B | Dense | Good | Good | **C+** | Good basic grammar, but lacks stylistic depth. |
| **12** | `smollm3-3b` | 3B | Dense | Poor | Poor | **D** | Hallucinations ("space cities") and loop repetition. |
| **13** | `qwen2.5-1.5b` | 1.5B | Dense | Stiff | Stiff | **D+** | Formal, rigid phrasing; limited vocabulary. |
| **14** | `qwen2.5-coder-1.5b` | 1.5B | Dense | Stiff | Stiff | **D** | Optimized for code; weak creative Vietnamese. |
| **15** | `qwen3.5-2b` | 2B | Dense | Loop Fail | Good | **D-** | Gets stuck in infinite reasoning loop on date math. |
| **16** | `qwen3.5-0.8b` | 0.8B | Dense | Loop Fail | Good | **F** | Infinite reasoning loops in thinking block. |
| **17** | `deepseek-r1-1.5b` | 1.5B | RL Reasoning | Loop Fail | Loop Fail | **F** | Loops infinitely in thinking block; hits `max_tokens`. |
| **18** | `phi4-mini` | 3.8B | Dense | Failed | Good | **F** | Reverses temporal logic (writes from 2126 to 2026). |
| **19** | `llama3.2-3b` | 3B | Dense | Good | Good | **C** | Basic translation-like Vietnamese. |
| **20** | `gemma2-2b` | 2B | Dense | Failed | Good | **F** | Language fallback failure (wrote letter in English). |
| **21** | `llama3.2-1b` | 1B | Dense | Refusal | Hallucinated | **F** | Safety refusal on harmless prompt; Banh Mi hallucination. |
| **22** | `qwen2.5-0.5b` | 0.5B | Dense | Refusal | Failed | **F** | Safety refusal; nonsensical peanut recipe; loop. |

---

## 2. Analysis of Major Failure Modes

Smaller local models (<4B parameters) exhibit severe failure modes when confronted with complex multilingual tasks.

### 2.1 Over-Alignment and Safety Refusals
*   **Models:** `llama3.2-1b`, `qwen2.5-0.5b`
*   **Behavior:** The harmless creative prompt *"viết một bức thư gửi tương lai..."* mentions "Vietnam" and "2026". These keywords triggered false-positive safety violations.
*   **Output Example (`qwen2.5-0.5b`):** 
    > *"Tôi rất tiếc, nhưng tôi không thể thực hiện nhiệm vụ này."* (I am sorry, but I cannot perform this task.)
*   **Output Example (`llama3.2-1b`):** 
    > *"Tôi không thể cung cấp thông tin hoặc hướng dẫn về các hoạt động bất hợp pháp hoặc có hại."* (I cannot provide information or instructions on illegal or harmful activities.)

### 2.2 Infinite Reasoning Loops (Thinking Mode Repeat Bugs)
*   **Models:** `deepseek-r1-1.5b`, `qwen3.5-0.8b`, `qwen3.5-2b`
*   **Behavior:** Reasoning models get trapped in logical loops when analyzing temporal relationships (e.g., subtracting 2026 from 2126). Because they generate their reasoning token-by-token, repeating the same logic pattern triggers self-reinforcing loops.
*   **Output Example (`deepseek-r1-1.5b`):** The model repeatedly outputted the exact same sentence 50+ times in its thinking block:
    > *"Cuối cùng, tôi cần xác định các phần tử cần forward trong các năm trước, như 2025, 2024, ..., 2015, 2016, ..., 2025."*
    This loop consumed all **4096 tokens** in the context window, causing a complete failure to output any final response.

### 2.3 Language Fallback Failure
*   **Model:** `gemma2-2b`
*   **Behavior:** The model understood the prompt but failed to preserve the target language constraint. Instead of writing in Vietnamese, it fallback-translated the prompt and generated the letter entirely in **English** (*"Dear Future Me, It's me, you, from 2026..."*).

### 2.4 Temporal Logic Reversal
*   **Model:** `phi4-mini` (3.8B)
*   **Behavior:** The model failed to grasp who was writing to whom. The prompt asked for a letter *from* 2026 *to* 2126. The model wrote a letter *from* 2126 thanking the people in 2026. It also relied heavily on unrendered template placeholders like `[Tên của bạn]` and `[Địa chỉ của bạn]`.

### 2.5 Severe Content Hallucinations
*   **Model:** `smollm3-3b`
*   **Behavior:** The model hallucinated surreal sci-fi concepts and repetitive grammar:
    > *"Tôi đang ngồi trên một chiếc bàn bằng nhựa, với một chiếc điện thoại mang hình dạng giống như một con chim..."*
    It listed bizarre categories like *"Khoáng học"*, *"Khoáng học môi trường"*, *"Khoáng học xã hội"*, and repeated its concluding sentence three times:
    > *"Tôi đang sống trong một thế giới mà không có sự cô đơn, sự phân biệt, và sự hy sinh. Tôi đang sống..."*
*   **Model:** `llama3.2-1b` (Reflect Task)
    It claimed that Vietnamese Banh Mi is deep-fried (*Bánh Mì chiên*) or stir-fried (*Bánh Mì xào*) in a pan with vegetables.
*   **Model:** `qwen2.5-0.5b` (Reflect Task)
    It recommended "White Peanuts" (*Đậu phộng trắng*) as a signature dish and completely failed the critique/revision steps, outputting static English template feedback text in Step 2 and Step 3 instead of performing self-critique.

### 2.6 Reflect Pipeline Execution (Critique & Revision)
*   **High-Tier Models (Gemma 4 26B/31B, Qwen 3.6 27B/35B):** Successfully completed the agentic loop. When the initial generation in Step 1 cut off mid-text due to token bounds, the Step 2 Self-Critique accurately identified the omissions (e.g. missing toppings, regional differences, raw cut-offs), and the Step 3 Revision successfully produced a complete, polished, and bilingual guide.
*   **Low-Tier Models (<3B):** Completely failed the agentic loop. They either generated frozen template text in English (like `qwen2.5-0.5b`) or completely ignored the critique inputs, repeating the exact same flawed text from Step 1 in Step 3 without any revisions.

---

## 3. Dense vs. Quantization-Aware Training (QAT) in Vietnamese

Quantization-Aware Training (QAT) is a significant architectural differentiator for local deployments, especially in non-English languages where standard post-training quantization (PTQ, like `Q4_K_M`) degrades performance.

*   **Syntax & Vocabulary Richness:** Both E2B and QAT E2B maintain correct Vietnamese grammar. However, `gemma4-qat-e2b` generates highly evocative, context-aware metaphors (e.g. *"mùi cà phê rang xay buổi sớm"*, *"cơn mưa rào bất chợt"*). Standard `gemma4-e2b` defaults to more formulaic and rigid vocabulary (*"sự pha trộn kỳ lạ"*, *"nhịp sống hối hả"*).
*   **Tonal Consistency:** QAT models display much higher tone stability. While standard PTQ models occasionally switch abruptly between conversational prose and dry bullet points, the QAT versions maintain the specified persona (e.g., reflective time-traveler or professional chef) consistently across long generations.

---

## 4. High-Tier Model Stylistic Comparisons (Qwen 3.6 vs. Gemma 4)

For parameters $\ge 12\text{B}$, models exhibit native-level Vietnamese fluency. However, their output styles differ depending on their training history:

### 4.1 Qwen 3.6 (27B & 35B-A3B)
*   **Strengths:** Highly structured, logical, and concise. Qwen excels at following negative constraints (e.g., "Answer short and concise") and stays strictly on-topic.
*   **Weaknesses:** Reasoning blocks are highly verbose and can contain unnecessary meta-commentary (e.g. repeating phrases like *"Done"*, *"Proceeds"*). The Vietnamese style is correct but leans formal and academic.

### 4.2 Gemma 4 (26B-A4B & 31B)
*   **Strengths:** Deeply atmospheric, creative, and literary. Gemma writes beautiful, flowing Vietnamese prose with rich cultural references.
*   **Weaknesses:** Weak instruction-following on length constraints. Gemma frequently ignores "answer short" constraints and generates long, detailed essays with heavy markdown formatting.

---

## 5. Deployment Recommendations for Vietnamese

1.  **Best Resource-Constrained Model (<3B):** **`gemma4-qat-e2b` (2.3B)**. It avoids refusals, loop bugs, and language fallbacks while generating excellent, natural Vietnamese prose.
2.  **Best CPU Throughput Model:** **`gemma4-qat-26b-a4b` (26B MoE)**. With only ~3.8B active parameters, it generates high-quality reasoning and creative writing in Vietnamese at over 11 tok/s, outperforming 4.5B dense models.
3.  **Best Overall Accuracy & Quality:** **`qwen3.6-35b-a3b` (35B MoE)**. It offers the best balance of reasoning, strict constraint-following, and natural Vietnamese formatting.
