from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

ROOT = Path('/Users/rAIph/Projects/agent-reflex')
LOG_DIR = Path('/Users/rAIph/Library/Logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

SERVICES = [
    {
        'name': 'agent-reflex-web',
        'pidfile': ROOT / '.agent-reflex-web.pid',
        'cmd': [str(ROOT / '.venv/bin/agent-reflex-web'), '--host', '127.0.0.1', '--port', '8765'],
        'stdout': LOG_DIR / 'agent-reflex-web.out.log',
        'stderr': LOG_DIR / 'agent-reflex-web.err.log',
    },
    {
        'name': 'cactus-needle',
        'pidfile': ROOT / '.cactus-needle.pid',
        'cmd': ['/opt/homebrew/bin/cactus', 'serve', 'Cactus-Compute/needle', '--host', '127.0.0.1', '--port', '8088', '--no-cloud-handoff'],
        'stdout': LOG_DIR / 'cactus-needle.out.log',
        'stderr': LOG_DIR / 'cactus-needle.err.log',
    },
]


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_existing(pidfile: Path) -> None:
    if not pidfile.exists():
        return
    try:
        pid = int(pidfile.read_text().strip())
    except ValueError:
        pidfile.unlink(missing_ok=True)
        return
    if is_running(pid):
        os.kill(pid, signal.SIGTERM)
    pidfile.unlink(missing_ok=True)


def start(service: dict[str, object]) -> int:
    pidfile = service['pidfile']
    assert isinstance(pidfile, Path)
    stop_existing(pidfile)
    stdout_path = service['stdout']
    stderr_path = service['stderr']
    cmd = service['cmd']
    assert isinstance(stdout_path, Path)
    assert isinstance(stderr_path, Path)
    assert isinstance(cmd, list)
    stdout = stdout_path.open('ab')
    stderr = stderr_path.open('ab')
    env = os.environ.copy()
    env['PATH'] = f"{ROOT / '.venv/bin'}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    process = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    pidfile.write_text(str(process.pid))
    print(f"{service['name']} pid={process.pid}")
    return process.pid


def main() -> int:
    for service in SERVICES:
        start(service)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
