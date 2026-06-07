# profile_client.py
import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--reasoning", action="store_true", help="Show [think] reasoning tokens")
parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
parser.add_argument("--output", type=str, default=None, help="Output file path (base for .txt tee and .json save)")
args = parser.parse_args()
SHOW_REASONING = args.reasoning

API_BASE = f"http://localhost:{args.port}/v1"
API_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"

PROMPTS = [
    ("Q01", "Tell me about software architecture. Answer short, concise, and correct."),
    ("Q02", "Explain how neural networks learn. Answer short, concise, and correct."),
    ("Q03", "What is the difference between TCP and UDP? Answer short, concise, and correct."),
    ("Q04", "How does garbage collection work in Python? Answer short, concise, and correct."),
    ("Q05", "Describe microservices. Answer short, concise, and correct."),
    ("Q06", "What is a closure in programming? Answer short, concise, and correct."),
    ("Q07", "Explain the CAP theorem. Answer short, concise, and correct."),
    ("Q08", "How does DNS resolution work? Answer short, concise, and correct."),
    ("Q09", "What are design patterns? Answer short, concise, and correct."),
    ("Q10", "Describe database transactions. Answer short, concise, and correct."),
]


async def profile_single_request(client: httpx.AsyncClient, prompt: str, model_name: str):
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": 4096,
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
    last_chunk = {}

    try:
        async with client.stream(
            "POST", API_URL, json=payload, timeout=120.0
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
                        last_chunk = data
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
            "ttft_ms": ttft * 1000,
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
    async with httpx.AsyncClient() as client:
        model_name = await fetch_model_name(client)
        print(f"Auto-detected model: {model_name}")

        prompts = PROMPTS
        num_prompts = len(prompts)

        results = []
        all_raw = []
        for i, (qid, prompt) in enumerate(prompts):
            print(f"\n  -> {qid} [{i + 1}/{num_prompts}]")
            print(f"     IN:  {prompt}")
            res = await profile_single_request(client, prompt, model_name)
            if res:
                results.append((qid, res))
                timings = res.get("server_timings", {})
                print(
                    f"     [{qid}] TTFT={res['ttft_ms']:.2f}ms Total={res['total_time_s']:.2f}s"
                )
                if timings:
                    print(f"     {format_server_timings_line(timings)}")
                all_raw.append({
                    "qid": qid,
                    "prompt": prompt,
                    "model": model_name,
                    "ttft_ms": res["ttft_ms"],
                    "total_time_s": res["total_time_s"],
                    "server_timings": timings,
                    "thinking_length": len(res.get("thinking", "")),
                    "response_length": len(res.get("response", "")),
                })
            else:
                print("     Failed.")
            await asyncio.sleep(0.5)

        if not results:
            print("[error] No data gathered.")
            return

        avg_ttft = sum(r["ttft_ms"] for _, r in results) / len(results)
        avg_total = sum(r["total_time_s"] for _, r in results) / len(results)

        has_server_timings = any(r.get("server_timings") for _, r in results)
        avg_server_tps = 0
        avg_server_tpot = 0
        avg_prompt_ms = 0
        total_predicted = 0
        total_predicted_ms = 0
        total_prompt_ms = 0
        if has_server_timings:
            for _, r in results:
                t = r.get("server_timings", {})
                if t:
                    total_predicted += t.get("predicted_n", 0)
                    total_predicted_ms += t.get("predicted_ms", 0)
                    total_prompt_ms += t.get("prompt_ms", 0)
            if total_predicted_ms > 0:
                avg_server_tps = total_predicted / (total_predicted_ms / 1000)
            if total_predicted > 0:
                avg_server_tpot = total_predicted_ms / total_predicted
            if has_server_timings:
                avg_prompt_ms = total_prompt_ms / sum(1 for _, r in results if r.get("server_timings"))

        print("\n================ PROFILE SUMMARY ================")
        print(f"[info] Model: {model_name}")
        print(f"[info] Questions: {len(results)}")
        print(f"[info] Average TTFT (client): {avg_ttft:.2f} ms")
        if has_server_timings:
            print(f"[info] Average Prompt Time (server): {avg_prompt_ms:.2f} ms")
            print(f"[info] Total Predicted Tokens (server): {total_predicted}")
            print(f"[info] Total Predicted Time (server): {total_predicted_ms:.2f} ms")
            print(f"[info] Average Decode Speed (server): {avg_server_tps:.2f} tokens/sec")
            print(f"[info] Average ms/token (server): {avg_server_tpot:.2f} ms")
        print(f"[time] Average Total Wall Duration: {avg_total:.2f} seconds")
        print("=================================================")

        if args.output:
            json_path = Path(args.output).with_suffix(".json")
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump({"model": model_name, "results": all_raw}, f)
            print(f"\n[info] Raw JSON saved to {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
