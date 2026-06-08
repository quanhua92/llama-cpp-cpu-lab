#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

# Color helpers
def print_pass(msg):
    print(f"\033[92m[PASS]\033[0m {msg}")

def print_fail(msg):
    print(f"\033[91m[FAIL]\033[0m {msg}")

def print_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
RESULTS_CPU = REPO_DIR / "results" / "cpu"
RESULTS_GPU = REPO_DIR / "results" / "gpu"
REPORTS_DIR = REPO_DIR / "reports"

# Load all results
def load_results(results_dir):
    data = {}
    for f in results_dir.glob("*.json"):
        stem = f.stem
        mode = "think" if "_think" in stem else "nothink"
        model_key = stem.replace("_think", "").replace("_nothink", "")
        
        with open(f) as fh:
            res_json = json.load(fh)
            
        questions = {}
        for q in res_json["results"]:
            qid = q["qid"]
            st = q.get("server_timings", {})
            questions[qid] = {
                "ttft_ms": q["ttft_ms"],
                "total_s": q["total_time_s"],
                "decode_speed": st.get("predicted_per_second", 0),
                "prompt_speed": st.get("prompt_per_second", 0),
                "predicted_n": st.get("predicted_n", 0),
                "predicted_ms": st.get("predicted_ms", 0),
                "prompt_n": st.get("prompt_n", 0),
                "prompt_ms": st.get("prompt_ms", 0),
            }
        
        n = len(questions)
        if n > 0:
            avg_ttft = sum(q["ttft_ms"] for q in questions.values()) / n
            avg_total = sum(q["total_s"] for q in questions.values()) / n
            total_pred_n = sum(q["predicted_n"] for q in questions.values())
            total_pred_ms = sum(q["predicted_ms"] for q in questions.values())
            avg_decode = (total_pred_n / (total_pred_ms / 1000.0)) if total_pred_ms > 0 else 0
            
            total_prompt_n = sum(q["prompt_n"] for q in questions.values())
            total_prompt_ms = sum(q["prompt_ms"] for q in questions.values())
            avg_prompt = (total_prompt_n / (total_prompt_ms / 1000.0)) if total_prompt_ms > 0 else 0
        else:
            avg_ttft = avg_total = avg_decode = avg_prompt = 0
            
        data[(model_key, mode)] = {
            "questions": questions,
            "avg_ttft": avg_ttft,
            "avg_total": avg_total,
            "avg_decode": avg_decode,
            "avg_prompt": avg_prompt
        }
    return data

def clean_val(val):
    val = val.strip().replace("**", "").replace("*", "").replace(",", "")
    m = re.search(r"[-+]?\d*\.\d+|\d+", val)
    if m:
        return m.group(0)
    return val

def check_standard_report(report_path, results_data, label):
    if not report_path.exists():
        print_fail(f"{label} report not found at {report_path}")
        return False
    
    content = report_path.read_text()
    success = True
    
    nothink_section = re.search(r"## Nothink Mode.*?\n(.*?)\n## Think Mode", content, re.DOTALL)
    think_section = re.search(r"## Think Mode.*?\n(.*?)\n## Notes", content, re.DOTALL)
    
    def parse_table(table_text):
        rows = []
        for line in table_text.strip().split("\n"):
            if not line.strip() or line.strip().startswith("|---") or line.strip().startswith("| Rank"):
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                prompt_val = parts[4].replace(",", "")
                rows.append({
                    "rank": parts[0],
                    "model": parts[1],
                    "params_or_size": parts[2],
                    "decode": float(parts[3]),
                    "prompt": float(prompt_val)
                })
        return rows

    if nothink_section:
        nt_rows = parse_table(nothink_section.group(1))
        for r in nt_rows:
            key = (r["model"], "nothink")
            if key in results_data:
                actual = results_data[key]
                dec_diff = abs(r["decode"] - actual["avg_decode"])
                pro_diff = abs(r["prompt"] - actual["avg_prompt"])
                if dec_diff > 0.15:
                    print_fail(f"{label} [nothink] {r['model']} Decode Mismatch: table={r['decode']}, actual={actual['avg_decode']:.2f}")
                    success = False
                if pro_diff > 0.15:
                    print_fail(f"{label} [nothink] {r['model']} Prompt Mismatch: table={r['prompt']}, actual={actual['avg_prompt']:.2f}")
                    success = False
            else:
                print_fail(f"{label} [nothink] model {r['model']} results not found in raw files")
                success = False
                
    if think_section:
        t_rows = parse_table(think_section.group(1))
        for r in t_rows:
            key = (r["model"], "think")
            if key in results_data:
                actual = results_data[key]
                dec_diff = abs(r["decode"] - actual["avg_decode"])
                pro_diff = abs(r["prompt"] - actual["avg_prompt"])
                if dec_diff > 0.15:
                    print_fail(f"{label} [think] {r['model']} Decode Mismatch: table={r['decode']}, actual={actual['avg_decode']:.2f}")
                    success = False
                if pro_diff > 0.15:
                    print_fail(f"{label} [think] {r['model']} Prompt Mismatch: table={r['prompt']}, actual={actual['avg_prompt']:.2f}")
                    success = False
            else:
                print_fail(f"{label} [think] model {r['model']} results not found in raw files")
                success = False
                
    if success:
        print_pass(f"{label} tables are fully verified.")
    return success

def check_qat_comparison(cpu_data):
    filepath = REPORTS_DIR / "gemma4-qat-comparison.md"
    if not filepath.exists():
        print_fail("gemma4-qat-comparison.md not found")
        return False
        
    content = filepath.read_text()
    success = True
    
    # TTFT table
    ttft_table = re.search(r"## TTFT \(ms\).*?\n(.*?)\n##", content, re.DOTALL)
    if ttft_table:
        lines = ttft_table.group(1).strip().split("\n")
        for line in lines:
            if "|" not in line or line.startswith("|---") or line.startswith("| Model"):
                continue
            raw_parts = [p.strip() for p in line.split("|")[1:-1]]
            model_sub = raw_parts[0].lower()
            m_q4 = f"gemma4-{model_sub}"
            m_qat = f"gemma4-qat-{model_sub}"
            
            q4_nt = float(clean_val(raw_parts[1]))
            qat_nt = float(clean_val(raw_parts[2]))
            q4_t = float(clean_val(raw_parts[3]))
            qat_t = float(clean_val(raw_parts[4]))
            
            actual_q4_nt = cpu_data[(m_q4, "nothink")]["avg_ttft"]
            actual_qat_nt = cpu_data[(m_qat, "nothink")]["avg_ttft"]
            actual_q4_t = cpu_data[(m_q4, "think")]["avg_ttft"]
            actual_qat_t = cpu_data[(m_qat, "think")]["avg_ttft"]
            
            if abs(q4_nt - actual_q4_nt) > 1.5:
                print_fail(f"Comparison [TTFT] {m_q4} NoThink: table={q4_nt}, actual={actual_q4_nt:.2f}")
                success = False
            if abs(qat_nt - actual_qat_nt) > 1.5:
                print_fail(f"Comparison [TTFT] {m_qat} NoThink: table={qat_nt}, actual={actual_qat_nt:.2f}")
                success = False
            if abs(q4_t - actual_q4_t) > 1.5:
                print_fail(f"Comparison [TTFT] {m_q4} Think: table={q4_t}, actual={actual_q4_t:.2f}")
                success = False
            if abs(qat_t - actual_qat_t) > 1.5:
                print_fail(f"Comparison [TTFT] {m_qat} Think: table={qat_t}, actual={actual_qat_t:.2f}")
                success = False
                
    # Decode table
    dec_table = re.search(r"## Decode Speed \(tok/s\).*?\n(.*?)\n##", content, re.DOTALL)
    if dec_table:
        lines = dec_table.group(1).strip().split("\n")
        for line in lines:
            if "|" not in line or line.startswith("|---") or line.startswith("| Model"):
                continue
            raw_parts = [p.strip() for p in line.split("|")[1:-1]]
            model_sub = raw_parts[0].lower()
            m_q4 = f"gemma4-{model_sub}"
            m_qat = f"gemma4-qat-{model_sub}"
            
            q4_nt = float(clean_val(raw_parts[1]))
            qat_nt = float(clean_val(raw_parts[2]))
            q4_t = float(clean_val(raw_parts[3]))
            qat_t = float(clean_val(raw_parts[4]))
            
            actual_q4_nt = cpu_data[(m_q4, "nothink")]["avg_decode"]
            actual_qat_nt = cpu_data[(m_qat, "nothink")]["avg_decode"]
            actual_q4_t = cpu_data[(m_q4, "think")]["avg_decode"]
            actual_qat_t = cpu_data[(m_qat, "think")]["avg_decode"]
            
            if abs(q4_nt - actual_q4_nt) > 0.1:
                print_fail(f"Comparison [Decode] {m_q4} NoThink: table={q4_nt}, actual={actual_q4_nt:.2f}")
                success = False
            if abs(qat_nt - actual_qat_nt) > 0.1:
                print_fail(f"Comparison [Decode] {m_qat} NoThink: table={qat_nt}, actual={actual_qat_nt:.2f}")
                success = False
            if abs(q4_t - actual_q4_t) > 0.1:
                print_fail(f"Comparison [Decode] {m_q4} Think: table={q4_t}, actual={actual_q4_t:.2f}")
                success = False
            if abs(qat_t - actual_qat_t) > 0.1:
                print_fail(f"Comparison [Decode] {m_qat} Think: table={qat_t}, actual={actual_qat_t:.2f}")
                success = False

    # Wall Duration table
    wall_table = re.search(r"## Wall Duration \(s\).*?\n(.*?)\n##", content, re.DOTALL)
    if wall_table:
        lines = wall_table.group(1).strip().split("\n")
        for line in lines:
            if "|" not in line or line.startswith("|---") or line.startswith("| Model"):
                continue
            raw_parts = [p.strip() for p in line.split("|")[1:-1]]
            model_sub = raw_parts[0].lower()
            m_q4 = f"gemma4-{model_sub}"
            m_qat = f"gemma4-qat-{model_sub}"
            
            q4_nt = float(clean_val(raw_parts[1]))
            qat_nt = float(clean_val(raw_parts[2]))
            q4_t = float(clean_val(raw_parts[3]))
            qat_t = float(clean_val(raw_parts[4]))
            
            actual_q4_nt = cpu_data[(m_q4, "nothink")]["avg_total"]
            actual_qat_nt = cpu_data[(m_qat, "nothink")]["avg_total"]
            actual_q4_t = cpu_data[(m_q4, "think")]["avg_total"]
            actual_qat_t = cpu_data[(m_qat, "think")]["avg_total"]
            
            if abs(q4_nt - actual_q4_nt) > 0.2:
                print_fail(f"Comparison [Wall] {m_q4} NoThink: table={q4_nt}, actual={actual_q4_nt:.2f}")
                success = False
            if abs(qat_nt - actual_qat_nt) > 0.2:
                print_fail(f"Comparison [Wall] {m_qat} NoThink: table={qat_nt}, actual={actual_qat_nt:.2f}")
                success = False
            if abs(q4_t - actual_q4_t) > 0.2:
                print_fail(f"Comparison [Wall] {m_q4} Think: table={q4_t}, actual={actual_q4_t:.2f}")
                success = False
            if abs(qat_t - actual_qat_t) > 0.2:
                print_fail(f"Comparison [Wall] {m_qat} Think: table={qat_t}, actual={actual_qat_t:.2f}")
                success = False
                
    if success:
        print_pass("gemma4-qat-comparison.md is fully verified.")
    return success

def check_qwen_vs_gemma(cpu_data):
    filepath = REPORTS_DIR / "qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md"
    if not filepath.exists():
        print_fail("qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md not found")
        return False
        
    content = filepath.read_text()
    success = True
    
    # Speed comparison no-think
    nt_section = re.search(r"## 1\. Speed Comparison.*?\n(.*?)\n### Think Mode", content, re.DOTALL)
    if nt_section:
        lines = nt_section.group(1).strip().split("\n")
        gemma_actual = cpu_data[("gemma4-qat-26b-a4b", "nothink")]
        qwen_actual = cpu_data[("qwen3.6-35b-a3b", "nothink")]
        
        for line in lines:
            if "|" not in line or line.startswith("|---") or line.startswith("| Metric"):
                continue
            raw_parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(raw_parts) < 3:
                continue
            metric = raw_parts[0]
            gem_val = float(clean_val(raw_parts[1]))
            qwen_val = float(clean_val(raw_parts[2]))
            
            if "TTFT" in line or "TTFT" in metric:
                if abs(gem_val - gemma_actual["avg_ttft"]) > 1.5:
                    print_fail(f"Qwen/Gemma NT [TTFT] Gemma: table={gem_val}, actual={gemma_actual['avg_ttft']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_ttft"]) > 1.5:
                    print_fail(f"Qwen/Gemma NT [TTFT] Qwen: table={qwen_val}, actual={qwen_actual['avg_ttft']:.2f}")
                    success = False
            elif "Decode" in line or "Decode" in metric:
                if abs(gem_val - gemma_actual["avg_decode"]) > 0.1:
                    print_fail(f"Qwen/Gemma NT [Decode] Gemma: table={gem_val}, actual={gemma_actual['avg_decode']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_decode"]) > 0.1:
                    print_fail(f"Qwen/Gemma NT [Decode] Qwen: table={qwen_val}, actual={qwen_actual['avg_decode']:.2f}")
                    success = False
            elif "wall" in line.lower() or "wall" in metric.lower():
                if abs(gem_val - gemma_actual["avg_total"]) > 0.2:
                    print_fail(f"Qwen/Gemma NT [Wall] Gemma: table={gem_val}, actual={gemma_actual['avg_total']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_total"]) > 0.2:
                    print_fail(f"Qwen/Gemma NT [Wall] Qwen: table={qwen_val}, actual={qwen_actual['avg_total']:.2f}")
                    success = False

    # Speed comparison think
    t_section = re.search(r"### Think Mode \(reasoning on\).*?\n(.*?)\n###", content, re.DOTALL)
    if t_section:
        lines = t_section.group(1).strip().split("\n")
        gemma_actual = cpu_data[("gemma4-qat-26b-a4b", "think")]
        qwen_actual = cpu_data[("qwen3.6-35b-a3b", "think")]
        
        for line in lines:
            if "|" not in line or line.startswith("|---") or line.startswith("| Metric"):
                continue
            raw_parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(raw_parts) < 3:
                continue
            metric = raw_parts[0]
            gem_val = float(clean_val(raw_parts[1]))
            qwen_val = float(clean_val(raw_parts[2]))
            
            if "TTFT" in line or "TTFT" in metric:
                if abs(gem_val - gemma_actual["avg_ttft"]) > 1.5:
                    print_fail(f"Qwen/Gemma T [TTFT] Gemma: table={gem_val}, actual={gemma_actual['avg_ttft']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_ttft"]) > 1.5:
                    print_fail(f"Qwen/Gemma T [TTFT] Qwen: table={qwen_val}, actual={qwen_actual['avg_ttft']:.2f}")
                    success = False
            elif "Decode" in line or "Decode" in metric:
                if abs(gem_val - gemma_actual["avg_decode"]) > 0.1:
                    print_fail(f"Qwen/Gemma T [Decode] Gemma: table={gem_val}, actual={gemma_actual['avg_decode']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_decode"]) > 0.1:
                    print_fail(f"Qwen/Gemma T [Decode] Qwen: table={qwen_val}, actual={qwen_actual['avg_decode']:.2f}")
                    success = False
            elif "wall" in line.lower() or "wall" in metric.lower():
                if abs(gem_val - gemma_actual["avg_total"]) > 0.2:
                    print_fail(f"Qwen/Gemma T [Wall] Gemma: table={gem_val}, actual={gemma_actual['avg_total']:.2f}")
                    success = False
                if abs(qwen_val - qwen_actual["avg_total"]) > 0.2:
                    print_fail(f"Qwen/Gemma T [Wall] Qwen: table={qwen_val}, actual={qwen_actual['avg_total']:.2f}")
                    success = False
                    
    if success:
        print_pass("qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md is fully verified.")
    return success

def main():
    print_info("Starting Local LLM Lab benchmark report verification...")
    
    # Load CPU & GPU results
    print_info("Loading raw JSON results...")
    cpu_data = load_results(RESULTS_CPU)
    gpu_data = load_results(RESULTS_GPU)
    print_info(f"Loaded {len(cpu_data)} CPU runs and {len(gpu_data)} GPU runs.")
    
    all_success = True
    
    # Check CPU report
    print_info("Verifying reports/cpu.md...")
    cpu_ok = check_standard_report(REPORTS_DIR / "cpu.md", cpu_data, "CPU Report")
    all_success = all_success and cpu_ok
    
    # Check GPU report
    print_info("Verifying reports/gpu.md...")
    gpu_ok = check_standard_report(REPORTS_DIR / "gpu.md", gpu_data, "GPU Report")
    all_success = all_success and gpu_ok
    
    # Check Gemma QAT comparison report
    print_info("Verifying reports/gemma4-qat-comparison.md...")
    qat_ok = check_qat_comparison(cpu_data)
    all_success = all_success and qat_ok
    
    # Check Qwen vs Gemma report
    print_info("Verifying reports/qwen3.6-35b-a3b-vs-gemma4-26b-a4b.md...")
    qwen_vs_gemma_ok = check_qwen_vs_gemma(cpu_data)
    all_success = all_success and qwen_vs_gemma_ok
    
    print("\n" + "="*50)
    if all_success:
        print_pass("All benchmark reports and tables are 100% accurate!")
        sys.exit(0)
    else:
        print_fail("Discrepancies found in one or more benchmark reports. Please review the failures above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
