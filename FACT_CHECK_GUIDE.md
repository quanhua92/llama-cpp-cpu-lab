# Local LLM Lab — Fact-Checking Guide

This guide outlines the standard operating procedure for verifying benchmark reports, model metadata, and example outputs when running new benchmarks or adding new models to the repository.

---

## 1. Verifying Computed Results

Whenever benchmarks are run (via `run_cpu_benchmarks.sh`), the raw outputs are saved in the `results/cpu/` directory. Use the following steps to verify that the tables in the reports are accurate:

### Step 1.1: Parse Raw Statistics
For each model and mode (e.g., `qwen3.6-35b-a3b_think.txt`), locate the `================ PROFILE SUMMARY ================` block at the bottom of the file. Ensure the following metrics match the tables:
*   **TTFT:** `Average Time to First Token (TTFT)` (ms)
*   **TPOT:** `Average Time per Output Token (TPOT)` (ms)
*   **Throughput:** `Estimated Generation Throughput` (tok/s)
*   **Wall Duration:** `Average Total Wall Duration` (seconds)

### Step 1.2: Calculate Delta Percentages ($\Delta$) Correctly
Do **NOT** truncate the decimal part. Always calculate the delta percentage using the raw unrounded numbers, then round the resulting percentage to the nearest integer:
$$\Delta\% = \text{round}\left( \frac{\text{Think} - \text{NoThink}}{\text{NoThink}} \times 100 \right)$$
*Example:* 
If NoThink Wall is `8.18s` and Think Wall is `33.13s`:
$$\Delta\% = \frac{33.13 - 8.18}{8.18} \times 100 = 305.01\% \rightarrow +305\%$$

### Step 1.3: Verify Table Bolding Rules
Check table cells that are bolded (which indicate the better/faster model):
*   **TTFT, TPOT, and Wall Duration:** Lower values are better. Bold the **lowest** value.
*   **Throughput (tok/s):** Higher values are better. Bold the **highest** value.

### Step 1.4: Verify Rankings
Check that the ranking list in `reports/cpu.md` matches the raw TPS values sorted in descending order. Ensure no adjacent entries are inverted (e.g., `9.2 tok/s` must rank higher than `9.1 tok/s`).

---

## 2. Verifying Example Generation Outputs

Example streaming captures are stored in `examples/cpu/`.
*   Verify that the metadata block at the bottom of each markdown file (e.g., `TTFT: 928ms | 10.6 tok/s | 169.0s total (1775 tokens)`) matches the details cited in comparison reports (like `reports/qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md`).
*   Ensure the persona prompts and Vietnamese fluency claims correspond exactly to the generated text in the files.

---

## 3. Fact-Checking External Model Information

Model details are configured in `serve_cpu.sh` and `serve_gpu.sh` under the `MODELS` associative array. For any model in this list, you must fact-check the following attributes using web searches and model cards:

### 3.1 Key Attributes to Verify
1.  **Architecture Type:**
    *   *Dense:* All parameters are computed on every token.
    *   *MoE (Mixture of Experts):* Sparse computation where only a subset of parameters (experts) is active. Verify the routing mechanism (e.g., top-8 routing, shared experts).
2.  **Parameter Counts:**
    *   Verify both **Total Parameters** and **Active Parameters** per token for MoE models (e.g., Gemma 4 26B-A4B has 25.2B total / ~3.8B active; Qwen 3.6 35B-A3B has 35B total / ~3B active).
3.  **File Size:**
    *   Verify the GGUF file size on disk for specific quantizations (e.g., Q4_K_M vs Q4_0 QAT). Standardize display units to 1 decimal place (e.g., `16.8 GB` instead of `16 GB`).
4.  **Context Length:**
    *   Check the native context window supported by the model base (e.g., 128K for Gemma 4 E2B/E4B, 256K for larger Gemma 4 variants, 262K for Qwen 3.6).
5.  **Input Types / Multimodality:**
    *   Verify what modalities the model officially supports (e.g., text-only, vision-language, audio input).
    *   *Note:* Even if a GGUF is deployed as text-only in `llama.cpp`, note its native capabilities. E2B, E4B, and 12B support audio and vision natively; 12B features an encoder-free unified design.
6.  **Quantization Method:**
    *   Identify if the model is quantized using post-training quantization (PTQ) like `Q4_K_M` or Quantization-Aware Training (QAT) like `Q4_0`.

---

## 4. Standard Search Queries

Use the following queries on HuggingFace, Google, or general search engines to fetch official specification sheets:

*   **For general specs and parameter sizes:**
    `"<Model Name>" "total parameters" OR "active parameters"`
    *Example:* `"gemma-4-26B-A4B" "active parameters"`
*   **For context lengths:**
    `"<Model Name>" "context window" OR "context length"`
    *Example:* `"Qwen 3.5" "context window"`
*   **For GGUF sizes:**
    `"<Model Name>" GGUF "<Quantization>" file size`
    *Example:* `"Qwen3.6-27B" GGUF "Q4_K_M" size`
*   **For architecture details:**
    `"<Model Name>" architecture OR "encoder-free" OR "experts"`
    *Example:* `"Gemma 4" "12B" "encoder-free"`

---

## 5. File References

*   Model definitions: [serve_cpu.sh](file:///Users/quan/workspace/local-llm-lab/serve_cpu.sh) and [serve_gpu.sh](file:///Users/quan/workspace/local-llm-lab/serve_gpu.sh)
*   CPU benchmarks: [reports/cpu.md](file:///Users/quan/workspace/local-llm-lab/reports/cpu.md)
*   Gemma 4 QAT report: [reports/gemma4-qat-comparison.md](file:///Users/quan/workspace/local-llm-lab/reports/gemma4-qat-comparison.md)
*   Qwen MoE comparison: [reports/qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md](file:///Users/quan/workspace/local-llm-lab/reports/qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md)
*   Curated models list: [README.md](file:///Users/quan/workspace/local-llm-lab/README.md)
