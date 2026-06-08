# Local LLM Lab — Fact-Checking Guide

This guide defines the standard operating procedure for verifying benchmark reports, model metadata, and example outputs when running new benchmarks or adding new models to the repository. Maintaining factual accuracy in these reports is critical for ensuring credible recommendations.

---

## 1. Verifying Computed Results (Internal Data)

Whenever benchmarks are run (via `run_cpu_benchmarks.sh` or `run_gpu_benchmarks.sh`), raw json/txt logs are written to the `results/` directory. When creating or updating markdown tables (in `reports/cpu.md`, `reports/gpu.md`, `reports/gemma4-qat-comparison.md`, etc.), verify the metrics using these rules.

### 1.1 Automated Table Verification
To prevent human error and typos, always run the automated validator script:
```bash
python3 scripts/verify_reports.py
```
This script parses the markdown tables in all report files and compares every cell's values against the raw JSON outputs in `results/cpu` and `results/gpu` using the exact mathematical definitions below. It outputs `[PASS]` or `[FAIL]` indicators.

### 1.2 Mathematical Formulas for Metrics
If you must manually verify or calculate stats, use the exact calculations below:

*   **Average TTFT (ms):** Arithmetic mean of `ttft_ms` across the 10 questions.
    $$\text{Avg TTFT} = \frac{1}{10} \sum_{i=1}^{10} \text{ttft\_ms}_i$$
*   **Average Wall Duration (s):** Arithmetic mean of `total_time_s` across the 10 questions.
    $$\text{Avg Wall} = \frac{1}{10} \sum_{i=1}^{10} \text{total\_time\_s}_i$$
*   **Average Decode Speed (tok/s):** Total predicted tokens divided by total predicted time. Do **NOT** average the per-question decode speeds.
    $$\text{Avg Decode} = \frac{\sum_{i=1}^{10} \text{predicted\_n}_i}{\sum_{i=1}^{10} \left( \frac{\text{predicted\_ms}_i}{1000} \right)}$$
*   **Average Prompt Speed (tok/s):** Total prompt tokens divided by total prompt time. Do **NOT** average the per-question prompt speeds.
    $$\text{Avg Prompt} = \frac{\sum_{i=1}^{10} \text{prompt\_n}_i}{\sum_{i=1}^{10} \left( \frac{\text{prompt\_ms}_i}{1000} \right)}$$

### 1.3 Delta Percentages ($\Delta\%$)
When comparing two models or modes, compute the percentage difference using raw, unrounded numbers first, and then round the final percentage to the nearest integer:
$$\Delta\% = \text{round}\left( \frac{\text{New} - \text{Baseline}}{\text{Baseline}} \times 100 \right)$$

*Example:* If No-Think Wall is `8.183s` and Think Wall is `33.128s`:
$$\Delta\% = \text{round}\left( \frac{33.128 - 8.183}{8.183} \times 100 \right) = \text{round}(304.839\%) \rightarrow +305\%$$

### 1.4 Table Formatting Rules
*   **Bolding:** Always bold the better performing model in each comparison row/cell.
    *   *TTFT, TPOT, and Wall Duration:* Lower values are better. Bold the **lowest** value.
    *   *Throughput / Speeds (tok/s):* Higher values are better. Bold the **highest** value.
*   **Rankings:** Order rankings strictly by average Decode Speed in descending order. Ensure no adjacent entries are inverted.
*   **Rounding Precision:**
    *   Sizes on disk: Standardize to `GB` or `MB` with 1 decimal place (e.g., `14.4 GB` instead of `14 GB`).
    *   Speeds: Standardize to 1 decimal place in lists/rankings (e.g., `11.9 tok/s`) and 2 decimal places in side-by-side comparison tables (e.g., `11.90 tok/s`).
    *   TTFT: Standardize to nearest integer in milliseconds (e.g., `616 ms`).

---

## 2. Fact-Checking External Model Information

When adding a new model to `serve_cpu.sh` and `serve_gpu.sh` under the `MODELS` associative array, you must fact-check and verify its specifications.

### 2.1 Key Metadata Attributes to Verify
1.  **Architecture Type:**
    *   *Dense:* All model parameters are computed for every token.
    *   *MoE (Mixture of Experts):* Sparse computation where only a subset of parameters is active per token. Verify the expert routing mechanism (e.g., how many experts are routed vs shared).
2.  **Parameter Counts:**
    *   Verify **Total Parameters** (all weights) and **Active Parameters** per token for MoE models (e.g., Gemma 4 26B-A4B has 25.2B total / ~3.8B active; Qwen 3.6 35B-A3B has 35B total / ~3B active).
3.  **Context Length:**
    *   Verify the native context window supported by the model base (e.g., 256K for Gemma 4 26B-A4B, 262K for Qwen 3.6).
4.  **Multimodality:**
    *   Verify what modalities the model officially supports natively (e.g., text-only, vision-language, audio input), even if our deployed GGUF is currently run text-only in `llama.cpp`. Note unified/encoder-free designs (e.g., Gemma 4 12B).
5.  **Quantization Method:**
    *   **PTQ (Post-Training Quantization):** Standard quants like `Q4_K_M`, `Q8_0`.
    *   **QAT (Quantization-Aware Training):** Models trained with quantization target active (usually Google's `Q4_0` QAT files). QAT models offer higher quality at comparable file sizes.

### 2.2 Standard Web Search Templates
Use these queries on Hugging Face or search engines to pull official model details:

*   **For parameter counts & MoE routing:**
    `"<Model Name>" "total parameters" OR "active parameters" OR "experts"`
    *Example:* `"gemma-4-26B-A4B" "active parameters"`
*   **For context lengths:**
    `"<Model Name>" "context window" OR "context length" OR "RoPE"`
    *Example:* `"Qwen 3.6" "context window"`
*   **For architectural details:**
    `"<Model Name>" "architecture" OR "encoder-free" OR "multimodal"`
    *Example:* `"Gemma 4" "12B" "encoder-free"`
*   **For quantization details:**
    `"<Model Name>" GGUF "<Quantization>" OR "QAT"`
    *Example:* `"gemma-4-E2B-it" "qat" "q4_0"`

---

## 3. Example Output Verification

Example captures are stored in `examples/cpu/` and `examples/gpu/`.
1.  Verify that the metadata block at the bottom of the example markdown file (e.g., `TTFT: 928ms | 10.6 tok/s | 169.0s total (1775 tokens)`) matches the details cited in the comparison reports exactly.
2.  Ensure that the persona claims (e.g., "professional chef persona", "literary tone") and fluency evaluations match the actual Vietnamese text generated in the example files.

---

## 4. Verifying Qualitative & Comparative Claims ("Best", "Top", "Similar")

When writing or reviewing summaries that make qualitative claims or compare model characteristics, use the following rules to verify that they are factual:

### 4.1 "Best" or "Top" Claims
*   **Performance Bests:** Statements declaring a model as "top" or "best" in speed must correspond directly to its rank in our benchmark reports (e.g., Qwen 2.5-0.5B is the "top" model for CPU/GPU throughput because it is ranked #1 in both `cpu.md` and `gpu.md`).
*   **Capabilities Bests:** Statements declaring a model "best" for a specific category (e.g., SmolLM3 3B as "best small model 2025") must be sourced from widely accepted public benchmarks (such as Hugging Face Open LLM Leaderboard v2) or detailed evaluation publications.
*   **Tone:** Avoid marketing hype or absolute phrases (e.g., "by far the best ever"). Instead, use objective, qualified phrasing (e.g., "consistently ranks top in its parameter class").

### 4.2 "Similar" Claims
*   **Similar Active Parameters / Size:** Claims that two models are "similar in size" or have "similar active parameters" (e.g., Gemma 4 26B-A4B and Gemma 4 E4B) must be supported by the parameter counts. A difference of less than 20% in active parameters qualifies as "similar active parameters" (e.g., ~3.8B active vs 4.5B active).
*   **Similar Speed / Throughput:** Claims that two models have "similar speed" (e.g., "similar decode throughput") must be verified against our benchmark tables. The average decode speeds must be within a 15% margin to be described as similar.
*   **Similar Architecture:** Claims that two models have "similar architecture" must be checked for key structural patterns (e.g., both are MoE models using standard top-8 expert routing, or both are dense models using GQA).

---

## 5. Checklists for Files to Update

When modifying benchmarks, the following files must remain consistent:
*   [ ] **Model Lists:** Check that the model exists in the `MODELS` lists in both [serve_cpu.sh](file:///Users/quan/workspace/local-llm-lab/serve_cpu.sh) and [serve_gpu.sh](file:///Users/quan/workspace/local-llm-lab/serve_gpu.sh).
*   [ ] **Model Key / Names:** Ensure the names match the directories and GGUF files perfectly.
*   [ ] **CPU Rankings:** Update [reports/cpu.md](file:///Users/quan/workspace/local-llm-lab/reports/cpu.md) using the output of `analyze_results.py`.
*   [ ] **GPU Rankings:** Update [reports/gpu.md](file:///Users/quan/workspace/local-llm-lab/reports/gpu.md) using the output of `analyze_results.py`.
*   [ ] **Model Description in README:** Update [README.md](file:///Users/quan/workspace/local-llm-lab/README.md)'s "Curated Models" table with accurate parameter counts, architectural summaries, and file sizes.
*   [ ] **Run Verification:** Run `python3 scripts/verify_reports.py` and verify all tests pass.
