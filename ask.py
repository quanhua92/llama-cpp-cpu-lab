# ask.py
import argparse
import asyncio
import json
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8888, help="Server port (default: 8888)")
parser.add_argument("--max-tokens", type=int, default=8192, help="Max tokens (default: 8192)")
parser.add_argument("prompt", help="Prompt to send")
args = parser.parse_args()

API_BASE = f"http://localhost:{args.port}/v1"
API_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"


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
        print(f"Model: {model_name}")
        print(f"{'='*60}")
        print(f"> {args.prompt}")
        print(f"{'='*60}")

        payload = {
            "messages": [{"role": "user", "content": args.prompt}],
            "stream": True,
            "max_tokens": args.max_tokens,
            "temperature": 0.0,
        }

        start_time = time.perf_counter()
        ttft = None
        prompt_tokens = 0
        completion_tokens = 0
        printed_thinking_header = False
        printed_response_header = False

        try:
            async with client.stream(
                "POST", API_URL, json=payload, timeout=120.0
            ) as response_stream:
                if response_stream.status_code != 200:
                    body = await response_stream.aread()
                    print(f"Server Error {response_stream.status_code}: {body.decode()}")
                    return

                async for chunk in response_stream.aiter_lines():
                    if not chunk.strip():
                        continue
                    if ttft is None:
                        ttft = time.perf_counter() - start_time
                    if chunk.startswith("data: ") and chunk != "data: [DONE]":
                        try:
                            data = json.loads(chunk[6:])
                            timings = data.get("timings", {})
                            if timings:
                                completion_tokens = timings.get("predicted_n", completion_tokens)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            reasoning = delta.get("reasoning_content", "")
                            if reasoning:
                                if not printed_thinking_header:
                                    print(f"\n{'[think]':>8} ", end="", flush=True)
                                    printed_thinking_header = True
                                print(reasoning, end="", flush=True)
                            if content:
                                if not printed_response_header:
                                    print(f"\n{'[out]':>8} ", end="", flush=True)
                                    printed_response_header = True
                                print(content, end="", flush=True)
                        except Exception:
                            pass

            total_duration = time.perf_counter() - start_time
            gen_time = total_duration - ttft if ttft else total_duration
            tok_per_sec = completion_tokens / gen_time if gen_time > 0 else 0

            print(f"\n{'='*60}")
            if ttft:
                print(f"TTFT: {ttft*1000:.0f}ms | {tok_per_sec:.1f} tok/s | {total_duration:.1f}s total ({completion_tokens} tokens)")
            else:
                print(f"Total: {total_duration:.1f}s")
        except Exception as e:
            print(f"Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
