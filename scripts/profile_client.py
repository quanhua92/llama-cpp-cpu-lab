# profile_client.py
import argparse
import asyncio

import time
from datetime import datetime

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--reasoning", action="store_true", help="Show [think] reasoning tokens")
parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
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
                    import json
                    try:
                        data = json.loads(chunk[6:])
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
        tpot = (
            (total_duration - ttft) / max(1, token_chunks - 1)
            if token_chunks > 1
            else 0
        )

        return {
            "ttft_ms": ttft * 1000,
            "total_time_s": total_duration,
            "chunks_generated": token_chunks,
            "tpot_ms": tpot * 1000,
            "thinking": thinking,
            "response": response,
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


async def main():
    async with httpx.AsyncClient() as client:
        model_name = await fetch_model_name(client)
        print(f"Auto-detected model: {model_name}")

        prompts = PROMPTS
        num_prompts = len(prompts)

        results = []
        for i, (qid, prompt) in enumerate(prompts):
            print(f"\n  -> {qid} [{i + 1}/{num_prompts}]")
            print(f"     IN:  {prompt}")
            res = await profile_single_request(client, prompt, model_name)
            if res:
                results.append((qid, res))
                print(
                    f"     [{qid}] TTFT={res['ttft_ms']:.2f}ms TPOT={res['tpot_ms']:.2f}ms Chunks={res['chunks_generated']} Total={res['total_time_s']:.2f}s"
                )
            else:
                print("     Failed.")
            await asyncio.sleep(0.5)

        if not results:
            print("[error] No data gathered.")
            return

        avg_ttft = sum(r["ttft_ms"] for _, r in results) / len(results)
        avg_total = sum(r["total_time_s"] for _, r in results) / len(results)
        avg_tpot = sum(r["tpot_ms"] for _, r in results) / len(results)

        print("\n================ PROFILE SUMMARY ================")
        print(f"[info] Average Time to First Token (TTFT): {avg_ttft:.2f} ms")
        print(f"[info] Average Time per Output Token (TPOT): {avg_tpot:.2f} ms")
        print(f"[info] Estimated Generation Throughput: {1000 / avg_tpot:.2f} tokens/sec")
        print(f"[time] Average Total Wall Duration: {avg_total:.2f} seconds")
        print("=================================================")


if __name__ == "__main__":
    asyncio.run(main())
