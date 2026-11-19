import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from graph import create_graph

BASE_DIR = Path(__file__).resolve().parent
FLASK_APP_PATH = (BASE_DIR / "data/e2e_testing_agent_app.py").resolve()
HOST, PORT = "127.0.0.1", 5000

app = create_graph()


async def run_workflow(query: str, target_url: str):
    """Run the LangGraph workflow"""
    initial_state = {
        "messages": [],
        "query": query,
        "actions": [],
        "target_url": target_url,
        "current_action": 0,
        "current_action_code": "",
        "aggregated_raw_actions": "",
        "script": None,
        "website_state": None,
        "error_message": None,
        "test_name": None,
    }
    return await app.ainvoke(initial_state)


def wait_for_port(host: str, port: int, timeout: float = 15.0) -> None:
    """Block until the Flask server accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise TimeoutError(f"Flask server not up on {host}:{port} after {timeout}s")


async def main():
    process = subprocess.Popen(
        [sys.executable, "-m", "flask", "run", "--host", HOST, "--port", str(PORT)],
        env={**os.environ, "FLASK_APP": str(FLASK_APP_PATH), "FLASK_DEBUG": "1"},
    )
    try:
        wait_for_port(HOST, PORT)

        query = (
            "Test a registration form that contains username, password and "
            "password confirmation fields. After submitting it, verify that "
            "registration was successful."
        )
        target_url = f"http://localhost:{PORT}"
        result = await run_workflow(query, target_url)
        print(result)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Flask app terminated.")


if __name__ == "__main__":
    asyncio.run(main())