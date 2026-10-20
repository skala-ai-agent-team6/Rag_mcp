"""Launch four temporary localhost MCP servers, verify calls, then stop them."""
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from fastmcp import Client


async def main():
    root = Path(__file__).resolve().parents[1]
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    payload = json.loads((root / "examples/search_request.json").read_text())
    calls = [
        ("observation", "normalize_observation", {"raw_text": payload["raw_text"],
         "origin": payload["origin"], "technician_confirmed": payload["technician_confirmed"]}),
        ("pcb", "interpret_pcb", {"labels": payload["pcb_labels"]}),
        ("damage", "interpret_damage", {"labels": payload["damage_labels"]}),
        ("rag", "retrieve_repair_context", {"request": payload}),
    ]
    processes, logs, results = [], [], {}
    try:
        for service, tool, arguments in calls:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            log = (runtime / f"{service}-http.log").open("w")
            logs.append(log)
            process = subprocess.Popen([
                sys.executable, "-m", "repair_mcp.cli", "serve", service,
                "--transport", "http", "--port", str(port)],
                cwd=root, stdout=log, stderr=log, env=os.environ.copy())
            processes.append(process)
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"{service} failed; see .runtime/{service}-http.log")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        raise TimeoutError(service)
                    await asyncio.sleep(0.1)
            async with Client(f"http://127.0.0.1:{port}/mcp", timeout=180) as client:
                result = await client.call_tool(tool, arguments)
                results[service] = result.data
                assert not result.is_error
                print(f"{service}: HTTP MCP OK", flush=True)
        assert results["observation"]["raw_text"] == results["rag"]["observation"]["raw_text"]
        assert results["rag"]["repair_cases"]
        assert len(results["rag"]["label_definitions"]) == 3
        assert results["rag"]["damage"]["domain_mismatch"]
        (runtime / "http-result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print("All four HTTP MCP services verified; results: .runtime/http-result.json")
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()


asyncio.run(main())
