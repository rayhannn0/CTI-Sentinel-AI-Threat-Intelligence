"""Locate Docker Desktop CLI on macOS and run Compose from the project root."""
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAC_CANDIDATES = [
    '/usr/local/bin/docker',
    '/opt/homebrew/bin/docker',
    '/Applications/Docker.app/Contents/Resources/bin/docker',
    str(Path.home() / '.docker/bin/docker'),
]

def docker_executable():
    candidates = [shutil.which('docker'), *MAC_CANDIDATES]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise RuntimeError(
        'Docker CLI was not found. Install Docker Desktop for Mac from '
        'https://docs.docker.com/desktop/setup/install/mac-install/ , open Docker Desktop, '
        'then check `docker --version` in Terminal. If VS Code cannot find Docker, '
        'restart VS Code after installation. The script cannot install Docker automatically.'
    )

def check_docker():
    docker = docker_executable()
    result = subprocess.run([docker, 'info'], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            'Docker CLI exists but Docker Engine is not running. Start Docker Desktop '
            'and wait for it to say Engine running. Details: ' + (result.stderr or result.stdout)[-600:]
        )
    result = subprocess.run([docker, 'compose', 'version'], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError('Docker Compose v2 is unavailable. Update Docker Desktop. ' + result.stderr[-600:])
    return docker

def compose(*args, check=True, capture_output=False):
    docker = check_docker()
    cmd = [docker, 'compose', *args]
    print('+', ' '.join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True,
                          capture_output=capture_output)
