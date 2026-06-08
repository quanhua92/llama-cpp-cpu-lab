# profile_context.py
import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser(description="Profile LLM with context-filled prompts (corpus-based)")
parser.add_argument("--corpus", type=str, default=None, help="Path to corpus text file")
parser.add_argument("--ctx-sizes", type=int, nargs="+", default=[2048, 8192, 32768, 65536],
                    help="Context sizes to test (default: 2048 8192 32768 65536)")
parser.add_argument("--ctx-fill", type=float, default=0.80,
                    help="Fraction of context to fill with corpus text (default: 0.80)")
parser.add_argument("--reasoning", action="store_true", help="Show [think] reasoning tokens")
parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
parser.add_argument("--output", type=str, default=None, help="Output file path (base for .txt tee and .json save)")
args = parser.parse_args()
SHOW_REASONING = args.reasoning

API_BASE = f"http://localhost:{args.port}/v1"
API_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"

QUESTION = "Summarize the key themes and writing style in the text above in 3-5 sentences."


CORPUS_URL = "https://www.gutenberg.org/files/1661/1661-0.txt"


def find_corpus():
    if args.corpus:
        path = Path(args.corpus)
        if path.is_file():
            return path
        print(f"ERROR: Corpus not found at {path}")
        raise SystemExit(1)
    corpus_dir = Path(__file__).resolve().parent.parent / "tuning"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    path = corpus_dir / "corpus.txt"
    if path.is_file():
        return path
    print(f"Corpus not found at {path}, downloading...")
    import urllib.request
    urllib.request.urlretrieve(CORPUS_URL, path)
    print(f"Downloaded corpus ({path.stat().st_size} bytes)")
    return path


def build_prompt(corpus_text: str, target_ctx: int, run_id: str) -> tuple[str, int]:
    corpus_bytes = len(corpus_text.encode("utf-8"))
    chars_per_token = max(1, corpus_bytes // 150000)
    target_tokens = int(target_ctx * args.ctx_fill)
    char_limit = target_tokens * chars_per_token
    fill_text = corpus_text[:char_limit]
    prompt = f"[ContextProfile {run_id}]\n\n{fill_text}\n\n{QUESTION}"
    return prompt, len(fill_text)


async def profile_single_request(client: httpx.AsyncClient, prompt: str, model_name: str, timeout: float = 300.0):
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": 512,
        "temperature": 0.0,
    }

    start_time = time.perf_counter()
    ttft = None
    token_chunks = 0
    thinking = ""
    response = ""
    printed_thinking_header = False
    printed_response_header = False
    server_timings = {}

    try:
        async with client.stream(
            "POST", API_URL, json=payload, timeout=timeout
        ) as response_stream:
            if response_stream.status_code != 200:
                print(f"Server Error: {response_stream.status_code}")
                return None

            async for chunk in response_stream.aiter_lines():
                if not chunk.strip():
                    continue
                if ttft is None:
                    ttft = time.perf_counter() - start_time
                token_chunks += 1
                if chunk.startswith("data: ") and chunk != "data: [DONE]":
                    try:
                        data = json.loads(chunk[6:])
                        if "timings" in data:
                            server_timings = data["timings"]
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning_content", "")
                        if reasoning:
                            if SHOW_REASONING:
                                if not printed_thinking_header:
                                    print(f"\n     {'[think]':>8} ", end="", flush=True)
                                    printed_thinking_header = True
                                print(reasoning, end="", flush=True)
                            thinking += reasoning
                        if content:
                            if not printed_response_header:
                                print(f"\n     {'[out]':>8} ", end="", flush=True)
                                printed_response_header = True
                            print(content, end="", flush=True)
                            response += content
                    except Exception:
                        pass

        total_duration = time.perf_counter() - start_time

        return {
            "ttft_ms": ttft * 1000 if ttft else None,
            "total_time_s": total_duration,
            "thinking": thinking,
            "response": response,
            "server_timings": server_timings,
        }
    except Exception as e:
        print(f"Request failed: {e}")
        return None


async def fetch_model_name(client: httpx.AsyncClient) -> str:
    try:
        resp = await client.get(MODELS_URL, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            if models:
                return models[0].get("id", "unknown")
    except Exception:
        pass
    return "unknown"


def format_server_timings_line(timings):
    if not timings:
        return "[timings] (none)"
    parts = []
    for key in ("prompt_n", "prompt_ms", "prompt_per_token_ms", "prompt_per_second",
                "predicted_n", "predicted_ms", "predicted_per_token_ms", "predicted_per_second",
                "cache_n", "cache_ms"):
        if key in timings:
            parts.append(f"{key}={timings[key]}")
    return "[timings] " + ", ".join(parts)


async def main():
    corpus_path = find_corpus()
    corpus_text = corpus_path.read_text()
    print(f"Corpus: {corpus_path} ({len(corpus_text)} chars)")
    print(f"Question: {QUESTION}")
    print(f"Context sizes: {args.ctx_sizes}")
    print(f"Context fill: {args.ctx_fill * 100:.0f}%")
    print()

    async with httpx.AsyncClient() as client:
        model_name = await fetch_model_name(client)
        print(f"Auto-detected model: {model_name}")

        num = len(args.ctx_sizes)
        results = []
        all_raw = []

        for i, ctx_size in enumerate(args.ctx_sizes):
            label = f"ctx{ctx_size}"
            run_id = f"{label}-{int(time.time() * 1000)}"
            prompt, fill_chars = build_prompt(corpus_text, ctx_size, run_id)
            est_tokens = len(prompt) // 4

            print(f"\n  -> {label} [{i + 1}/{num}] (prompt: ~{est_tokens} tokens, {fill_chars} chars fill)")
            res = await profile_single_request(client, prompt, model_name, timeout=300.0)
            if res:
                results.append((label, res, ctx_size, est_tokens, fill_chars))
                timings = res.get("server_timings", {})
                ttft_str = f"{res['ttft_ms']:.2f}ms" if res["ttft_ms"] else "N/A"
                print(
                    f"     [{label}] TTFT={ttft_str} Total={res['total_time_s']:.2f}s"
                )
                if timings:
                    print(f"     {format_server_timings_line(timings)}")
                all_raw.append({
                    "label": label,
                    "ctx_size": ctx_size,
                    "est_prompt_tokens": est_tokens,
                    "fill_chars": fill_chars,
                    "model": model_name,
                    "ttft_ms": res["ttft_ms"],
                    "total_time_s": res["total_time_s"],
                    "server_timings": timings,
                    "thinking_length": len(res.get("thinking", "")),
                    "response_length": len(res.get("response", "")),
                })
            else:
                print(f"     [{label}] Failed.")
            await asyncio.sleep(1.0)

        if not results:
            print("[error] No data gathered.")
            return

        print("\n================ CONTEXT PROFILE SUMMARY ================")
        print(f"[info] Model: {model_name}")
        print(f"[info] Runs: {len(results)}")
        print(f"{'label':<12} {'ctx':>6} {'prompt_n':>9} {'cache_n':>8} {'fill_chars':>10} {'TTFT':>8} {'prompt_ms':>10} {'prefill_t/s':>12} {'pred_n':>7} {'pred_ms':>9} {'tok/s':>8} {'total':>7}")
        print("-" * 112)

        total_predicted = 0
        total_predicted_ms = 0
        total_prompt_ms = 0
        has_server_timings = False

        for label, res, ctx_size, est_tokens, fill_chars in results:
            timings = res.get("server_timings", {})
            ttft_str = f"{res['ttft_ms']:.0f}ms" if res["ttft_ms"] else "N/A"
            prompt_ms = timings.get("prompt_ms", 0)
            prompt_n = timings.get("prompt_n", 0)
            cache_n = timings.get("cache_n", 0)
            prompt_tps = timings.get("prompt_per_second", 0)
            pred_n = timings.get("predicted_n", 0)
            pred_ms = timings.get("predicted_ms", 0)
            tps = pred_n / (pred_ms / 1000) if pred_ms > 0 else 0

            if timings:
                has_server_timings = True
                total_predicted += pred_n
                total_predicted_ms += pred_ms
                total_prompt_ms += prompt_ms

            print(f"{label:<12} {ctx_size:>6} {prompt_n:>9} {cache_n:>8} {fill_chars:>10} {ttft_str:>8} {prompt_ms:>9.0f}ms {prompt_tps:>11.0f} {pred_n:>7} {pred_ms:>8.0f}ms {tps:>7.1f} {res['total_time_s']:>6.1f}s")

        if has_server_timings:
            avg_server_tps = total_predicted / (total_predicted_ms / 1000) if total_predicted_ms > 0 else 0
            print(f"\n[info] Total Predicted Tokens: {total_predicted}")
            print(f"[info] Average Decode Speed (server): {avg_server_tps:.2f} tokens/sec")
        print("=========================================================")

        if args.output:
            json_path = Path(args.output).with_suffix(".json")
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump({
                    "model": model_name,
                    "corpus": str(corpus_path),
                    "ctx_fill": args.ctx_fill,
                    "results": all_raw,
                }, f, indent=2)
            print(f"\n[info] Raw JSON saved to {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
