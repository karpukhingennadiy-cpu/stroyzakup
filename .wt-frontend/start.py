#!/usr/bin/env python
"""Минитендер.рф — запуск backend + frontend одной командой.

Использование:
    python start.py            # dev-режим (Next.js dev server с hot-reload)
    python start.py --prod     # prod-режим (next start, требует собранный .next)

Остановка: Enter или Ctrl+C — оба сервера будут корректно завершены.
"""
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

BACKEND_PORT = 8000
FRONTEND_PORT = 3000

BUNDLED_NODE = r"C:\Users\karpu\AppData\Local\Programs\kimi-desktop\resources\resources\runtime\node.exe"


def find_node() -> str:
    """Ищем node: сначала в PATH, затем встроенный runtime Kimi."""
    node = shutil.which("node")
    if node:
        return node
    if os.path.exists(BUNDLED_NODE):
        return BUNDLED_NODE
    sys.exit("ОШИБКА: node.exe не найден ни в PATH, ни во встроенном runtime.")


def find_uv() -> str | None:
    uv = shutil.which("uv")
    if uv:
        return uv
    # uv из daimon-bundle (Git Bash окружение)
    candidate = r"C:\Users\karpu\AppData\Roaming\kimi-desktop\daimon-bundle\runtime\uv\uv.exe"
    return candidate if os.path.exists(candidate) else None


def wait_http(url: str, timeout: int = 60) -> bool:
    """Ждём, пока URL начнёт отвечать (любой HTTP-код)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):
                return True
        except urllib.error.HTTPError:
            return True  # сервер отвечает, пусть даже 401/404
        except Exception:
            time.sleep(1)
    return False


def stream_logs(proc: subprocess.Popen, prefix: str):
    """Пересылаем stdout процесса в консоль с префиксом."""
    for line in proc.stdout:
        print(f"[{prefix}] {line}", end="")


def main():
    prod = "--prod" in sys.argv
    procs: list[tuple[str, subprocess.Popen]] = []

    uv = find_uv()
    node = find_node()

    # ---------- Backend ----------
    print(f"[1/2] Django backend -> http://localhost:{BACKEND_PORT}")
    backend_env = os.environ.copy()
    backend_env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    if uv:
        backend_cmd = [uv, "run", "python", "manage.py",
                       "runserver", f"127.0.0.1:{BACKEND_PORT}"]
    else:
        # fallback: python из .venv
        venv_py = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
        backend_cmd = [venv_py, "manage.py", "runserver", f"127.0.0.1:{BACKEND_PORT}"]
    backend = subprocess.Popen(
        backend_cmd, cwd=BACKEND_DIR, env=backend_env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    procs.append(("django", backend))
    threading.Thread(target=stream_logs, args=(backend, "django"), daemon=True).start()

    # ---------- Frontend ----------
    print(f"[2/2] Next.js frontend -> http://localhost:{FRONTEND_PORT} ({'prod' if prod else 'dev'})")
    next_bin = os.path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next")
    if not os.path.exists(next_bin):
        for name, p in procs:
            p.kill()
        sys.exit("ОШИБКА: node_modules не найден. Выполните 'npm install' в папке frontend.")
    mode_args = ["start", "-p", str(FRONTEND_PORT)] if prod else ["dev", "-p", str(FRONTEND_PORT)]
    frontend = subprocess.Popen(
        [node, next_bin, *mode_args], cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    procs.append(("next", frontend))
    threading.Thread(target=stream_logs, args=(frontend, "next"), daemon=True).start()

    # ---------- Health checks ----------
    print("\nОжидаю готовности серверов...")
    be_ok = wait_http(f"http://localhost:{BACKEND_PORT}/api/", timeout=90)
    fe_ok = wait_http(f"http://localhost:{FRONTEND_PORT}/", timeout=120)

    print("\n" + "=" * 56)
    print(f"  Backend:  {'OK' if be_ok else 'НЕ ОТВЕЧАЕТ'}  http://localhost:{BACKEND_PORT}/api/")
    print(f"  Admin:                          http://localhost:{BACKEND_PORT}/admin/")
    print(f"  Frontend: {'OK' if fe_ok else 'НЕ ОТВЕЧАЕТ'}  http://localhost:{FRONTEND_PORT}")
    print("=" * 56)
    print("\nНажмите Enter или Ctrl+C для остановки серверов...\n")

    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    # ---------- Shutdown ----------
    print("\nОстанавливаю серверы...")
    for name, p in procs:
        if p.poll() is None:
            try:
                p.send_signal(signal.CTRL_BREAK_EVENT)
            except Exception:
                p.terminate()
    for name, p in procs:
        try:
            p.wait(timeout=8)
            print(f"  {name}: остановлен")
        except Exception:
            p.kill()
            print(f"  {name}: принудительно завершён")
    print("Готово.")


if __name__ == "__main__":
    main()
