#!/usr/bin/env python3
"""
GestureFlow AI Unified Launcher (Phase 6A.3).

Starts both the FastAPI backend and React/Vite frontend in a single command,
verifies service health, opens the application in the default browser,
and monitors child processes with graceful shutdown handling.

Usage:
    python run.py [--no-browser] [--backend-port PORT] [--frontend-port PORT]
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_HOST = "localhost"
DEFAULT_FRONTEND_PORT = 5173


def find_python_interpreter() -> str:
    """
    Locate the Python virtual environment interpreter for the backend.
    Prefers backend/.venv, falls back to .venv, or sys.executable.
    """
    candidates = [
        BACKEND_DIR / ".venv" / "Scripts" / "python.exe",
        BACKEND_DIR / ".venv" / "bin" / "python",
        ROOT_DIR / ".venv" / "Scripts" / "python.exe",
        ROOT_DIR / ".venv" / "bin" / "python",
    ]

    for cand in candidates:
        if cand.is_file():
            return str(cand.resolve())

    # Fallback: check if sys.executable has uvicorn available
    try:
        res = subprocess.run(
            [sys.executable, "-c", "import uvicorn, fastapi"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return sys.executable
    except Exception:
        pass

    # Default fallback
    return sys.executable


def find_npm_executable() -> str:
    """Locate npm command executable across platforms."""
    npm_name = "npm.cmd" if sys.platform == "win32" else "npm"
    npm_path = shutil.which(npm_name)
    if npm_path:
        return npm_path

    # Fallback to plain 'npm' if npm.cmd not found
    npm_fallback = shutil.which("npm")
    if npm_fallback:
        return npm_fallback

    raise RuntimeError(
        "Node package manager (npm) was not found on PATH. "
        "Please ensure Node.js and npm are installed."
    )


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a network port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def check_backend_health(url: str, timeout: float = 1.0) -> Tuple[bool, Optional[dict]]:
    """
    Check if the GestureFlow AI backend is online and healthy.
    Returns (is_healthy, response_data).
    """
    health_endpoint = f"{url.rstrip('/')}/health"
    try:
        req = urllib.request.Request(
            health_endpoint,
            headers={"User-Agent": "GestureFlow-Launcher/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                if payload.get("status") == "ok" and payload.get("application") == "GestureFlow AI":
                    return True, payload
    except Exception:
        pass
    return False, None


def check_frontend_ready(url: str, timeout: float = 1.0) -> bool:
    """Check if the Vite frontend server is responding."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GestureFlow-Launcher/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304)
    except Exception:
        return False


def wait_for_backend_ready(backend_url: str, max_timeout: float = 30.0) -> bool:
    """Poll backend health check endpoint until ready or timeout."""
    start_time = time.time()
    while time.time() - start_time < max_timeout:
        healthy, _ = check_backend_health(backend_url, timeout=0.8)
        if healthy:
            return True
        time.sleep(0.3)
    return False


def wait_for_frontend_ready(frontend_url: str, max_timeout: float = 30.0) -> bool:
    """Poll frontend server until responsive or timeout."""
    start_time = time.time()
    while time.time() - start_time < max_timeout:
        if check_frontend_ready(frontend_url, timeout=0.8):
            return True
        time.sleep(0.3)
    return False


def terminate_process_tree(proc: subprocess.Popen) -> None:
    """Cleanly terminate a child process and all its subprocesses."""
    if proc is None or proc.poll() is not None:
        return

    pid = proc.pid
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> int:
    # Ensure stdout flushes immediately
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description="GestureFlow AI Unified Launcher")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT, help="Backend port")
    parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT, help="Frontend port")
    args = parser.parse_args()

    backend_url = f"http://{DEFAULT_BACKEND_HOST}:{args.backend_port}"
    frontend_url = f"http://{DEFAULT_FRONTEND_HOST}:{args.frontend_port}"

    print("GestureFlow AI Launcher\n")

    backend_proc: Optional[subprocess.Popen] = None
    frontend_proc: Optional[subprocess.Popen] = None

    try:
        # Step 1: Manage Backend Process
        print("[STARTING] Backend...")

        # Check if backend port is already in use
        if is_port_in_use(DEFAULT_BACKEND_HOST, args.backend_port):
            healthy, info = check_backend_health(backend_url)
            if healthy:
                print(f"[READY] Backend: {backend_url} (reusing active GestureFlow AI instance)")
            else:
                print(
                    f"[ERROR] Port {args.backend_port} is already in use by another application. "
                    f"Please free port {args.backend_port} or run with --backend-port <PORT>."
                )
                return 1
        else:
            python_exe = find_python_interpreter()
            backend_cmd = [
                python_exe,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                DEFAULT_BACKEND_HOST,
                "--port",
                str(args.backend_port),
            ]

            env = os.environ.copy()
            env["PYTHONPATH"] = str(BACKEND_DIR)

            backend_proc = subprocess.Popen(
                backend_cmd,
                cwd=str(ROOT_DIR),
                env=env,
            )

            # Wait for backend health check
            if not wait_for_backend_ready(backend_url, max_timeout=25.0):
                print(f"[ERROR] Backend failed to report healthy on {backend_url}")
                if backend_proc.poll() is not None:
                    out = backend_proc.stdout.read() if backend_proc.stdout else ""
                    print(f"Backend output:\n{out[:500]}")
                terminate_process_tree(backend_proc)
                return 1

            print(f"[READY] Backend: {backend_url}\n")

        # Step 2: Manage Frontend Process
        print("[STARTING] Frontend...")

        if is_port_in_use(DEFAULT_FRONTEND_HOST, args.frontend_port):
            if check_frontend_ready(frontend_url):
                print(f"[READY] Frontend: {frontend_url} (reusing active instance)")
            else:
                print(f"[READY] Frontend port {args.frontend_port} active.")
        else:
            npm_cmd = find_npm_executable()
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=str(ROOT_DIR),
            )

            # Wait for frontend readiness
            if not wait_for_frontend_ready(frontend_url, max_timeout=25.0):
                print(f"[ERROR] Frontend failed to respond on {frontend_url}")
                terminate_process_tree(frontend_proc)
                if backend_proc:
                    terminate_process_tree(backend_proc)
                return 1

            print(f"[READY] Frontend: {frontend_url}\n")

        print("[READY] All services running.\n")
        print(f"Application: {frontend_url}")

        if not args.no_browser:
            try:
                webbrowser.open(frontend_url)
            except Exception as e:
                print(f"Notice: Could not automatically open browser ({e}). Please navigate to {frontend_url}")

        print("\nPress Ctrl+C to stop all services.")

        # Supervise child processes
        while True:
            time.sleep(0.5)
            if backend_proc and backend_proc.poll() is not None:
                print(f"\n[ALERT] Backend process terminated unexpectedly (exit code {backend_proc.returncode}).")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print(f"\n[ALERT] Frontend process terminated unexpectedly (exit code {frontend_proc.returncode}).")
                break

    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping all services...")
    finally:
        if frontend_proc:
            terminate_process_tree(frontend_proc)
            print("[SHUTDOWN] Frontend stopped.")
        if backend_proc:
            terminate_process_tree(backend_proc)
            print("[SHUTDOWN] Backend stopped.")
        print("[SHUTDOWN] All services terminated cleanly.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
